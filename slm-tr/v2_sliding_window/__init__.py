"""
v2 - Sliding Window Lateral Movement Detection Package
Provides loaders, trainers, stream detectors, and evaluators for multi-event temporal context.
"""

from v2_sliding_window.data_loader import (
    load_v2_dataset, 
    load_v2_for_decoder, 
    format_event_text, 
    format_sliding_window_text,
    generate_windowed_dataframe
)

__all__ = [
    "load_v2_dataset",
    "load_v2_for_decoder",
    "format_event_text",
    "format_sliding_window_text",
    "generate_windowed_dataframe"
]
