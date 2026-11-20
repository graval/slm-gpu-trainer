"""
EdgeShield: Hierarchical Dual-Head Threat Interception & Attribution Model
Level 1 (Primary): Binary Invariant Threat Interception (Normal vs Lateral Movement / Attack)
Level 2 (Auxiliary): Multi-Task TTP Attribution (EoRS, EoHT, LotL, Tool Transfer, Remote Exploit)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoConfig

class HierarchicalThreatDetector(nn.Module):
    def __init__(self, model_name_or_path: str = "microsoft/deberta-v3-small", num_subtypes: int = 6):
        super().__init__()
        self.config = AutoConfig.from_pretrained(model_name_or_path)
        self.backbone = AutoModel.from_pretrained(model_name_or_path, config=self.config)
        hidden_dim = getattr(self.config, "hidden_size", getattr(self.config, "dim", 768))
        
        # Level 1: Primary Threat Interception Head (Binary: Normal vs Malicious)
        self.threat_head = nn.Sequential(
            nn.Linear(hidden_dim, 256),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(256, 2)
        )
        
        # Level 2: Auxiliary TTP Attribution Head (Multi-Class Subtypes)
        self.subtype_head = nn.Sequential(
            nn.Linear(hidden_dim, 256),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_subtypes)
        )
        
        # Contrastive Projection Head (for invariant feature clustering)
        self.projection_head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64)
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        threat_labels: torch.Tensor = None,
        subtype_labels: torch.Tensor = None,
        alpha: float = 0.5,
        temperature: float = 0.07
    ):
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        # Extract [CLS] token embedding
        cls_rep = outputs.last_hidden_state[:, 0, :]
        
        threat_logits = self.threat_head(cls_rep)
        subtype_logits = self.subtype_head(cls_rep)
        projections = F.normalize(self.projection_head(cls_rep), dim=-1)
        
        loss = None
        loss_dict = {}
        if threat_labels is not None:
            # 1. Primary Threat Loss (CrossEntropy)
            ce_threat = F.cross_entropy(threat_logits, threat_labels)
            
            # 2. Auxiliary Subtype Loss (weighted only on actual attack samples)
            attack_mask = (threat_labels == 1)
            if attack_mask.sum() > 0 and subtype_labels is not None:
                ce_subtype = F.cross_entropy(subtype_logits[attack_mask], subtype_labels[attack_mask])
            elif subtype_labels is not None:
                ce_subtype = F.cross_entropy(subtype_logits, subtype_labels)
            else:
                ce_subtype = torch.tensor(0.0, device=input_ids.device)
                
            # 3. Supervised Contrastive Loss on threat_labels (pull attacks together, push normal away)
            sim_matrix = torch.matmul(projections, projections.T) / temperature
            labels_eq = torch.eq(threat_labels.unsqueeze(0), threat_labels.unsqueeze(1)).float()
            
            # Mask out self-contrast
            diag_mask = torch.eye(input_ids.size(0), dtype=torch.bool, device=input_ids.device)
            sim_matrix.masked_fill_(diag_mask, -1e9)
            labels_eq.masked_fill_(diag_mask, 0.0)
            
            exp_sim = torch.exp(sim_matrix)
            log_prob = sim_matrix - torch.log(exp_sim.sum(dim=1, keepdim=True) + 1e-9)
            mean_log_prob_pos = (labels_eq * log_prob).sum(dim=1) / (labels_eq.sum(dim=1) + 1e-9)
            scl_loss = -mean_log_prob_pos.mean()
            
            # Unified Multi-Task Loss
            loss = ce_threat + (alpha * ce_subtype) + (0.1 * scl_loss)
            loss_dict = {
                "total_loss": loss.item(),
                "ce_threat": ce_threat.item(),
                "ce_subtype": ce_subtype.item(),
                "scl_loss": scl_loss.item()
            }
            
        return {
            "loss": loss,
            "loss_dict": loss_dict,
            "threat_logits": threat_logits,
            "subtype_logits": subtype_logits,
            "cls_rep": cls_rep
        }
