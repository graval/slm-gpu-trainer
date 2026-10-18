Param(
    [string]$DocxPath,
    [string]$PdfPath
)

$ErrorActionPreference = "Stop"

try {
    Write-Host "[*] Launching Microsoft Word COM Object..."
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

    Write-Host "[*] Opening Document: $DocxPath"
    $doc = $word.Documents.Open($DocxPath, $false, $true)

    Write-Host "[*] Exporting to PDF: $PdfPath"
    # 17 = wdFormatPDF
    $wdFormatPDF = 17
    $doc.SaveAs([ref]$PdfPath, [ref]$wdFormatPDF)

    $doc.Close([ref]$false)
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    Write-Host "[+] Successfully generated PDF: $PdfPath"
} catch {
    Write-Error "Failed to convert DOCX to PDF: $_"
    if ($word) {
        $word.Quit()
    }
    exit 1
}
