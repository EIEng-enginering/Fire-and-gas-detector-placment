# Rev F: automated native Microsoft Office/PDF read-back of synthetic report outputs.
# Opens copies READ-ONLY via COM, records formula/literal-text evidence and exports
# Word to PDF for rendering. Automated evidence only; human visual review is separate.
param([Parameter(Mandatory=$true)][string]$ReportDir,[Parameter(Mandatory=$true)][string]$OutDir,[ValidateSet('Excel','Word')][string]$Part='Excel')
# Run each part separately under a caller watchdog; an invisible Office prompt can block COM indefinitely.
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$rec=[ordered]@{tool='rev_f_office_check.ps1';report_dir=$ReportDir;utc=(Get-Date).ToUniversalTime().ToString('o');qualification='UNVERIFIED AUTOMATED OFFICE READ-BACK';human_visual_review='NOT PERFORMED BY THIS SCRIPT'}
$xlsx=Join-Path $ReportDir 'Registers.xlsx'; $docx=Join-Path $ReportDir 'Study.docx'
$excel=$null; $word=$null
if ($Part -eq 'Excel') { try {
  $excel=New-Object -ComObject Excel.Application; $excel.Visible=$false; $excel.DisplayAlerts=$false
  $rec.excel_version=$excel.Version
  $wb=$excel.Workbooks.Open($xlsx,0,$true)
  $sheets=@(); $formulas=0; $eqText=0; $cells=0; $samples=@()
  foreach ($ws in $wb.Worksheets) {
    $ur=$ws.UsedRange; $rows=$ur.Rows.Count; $cols=$ur.Columns.Count
    $sheets+=[ordered]@{name=$ws.Name;rows=$rows;columns=$cols}
    foreach ($c in $ur.Cells) {
      $cells++
      if ($c.HasFormula) { $formulas++ }
      $t=[string]$c.Text
      if ($t.StartsWith('=')) { $eqText++; if ($samples.Count -lt 5) { $samples+=($ws.Name+'!'+$c.Address($false,$false)+' '+$t.Substring(0,[Math]::Min(60,$t.Length))) } }
    }
  }
  $wb.Close($false)
  $rec.excel=[ordered]@{opened='PASS';sheets=$sheets;cells_scanned=$cells;formula_cells=$formulas;literal_equals_text_cells=$eqText;literal_equals_samples=$samples;status=$(if ($formulas -eq 0) {'PASS'} else {'FAIL'})}
} catch { $rec.excel=[ordered]@{opened='FAIL';error=$_.Exception.Message} } finally { if ($excel) { $excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } } }
if ($Part -eq 'Word') { try {
  $word=New-Object -ComObject Word.Application; $word.Visible=$false; $word.DisplayAlerts=0
  $rec.word_version=$word.Version
  $doc=$word.Documents.Open($docx,$false,$true)
  $pages=$doc.ComputeStatistics(2); $tables=$doc.Tables.Count; $text=$doc.Content.Text
  $pdf=Join-Path $OutDir 'Study_WORD_EXPORT.pdf'
  $doc.ExportAsFixedFormat($pdf,17)
  $doc.Close(0)
  $rec.word=[ordered]@{opened='PASS';pages=$pages;tables=$tables;characters=$text.Length;contains_BLOCKED=($text -match 'BLOCKED');contains_UNVERIFIED=($text -match 'UNVERIFIED');exported_pdf=(Split-Path $pdf -Leaf);exported_pdf_bytes=(Get-Item $pdf).Length;status='PASS'}
} catch { $rec.word=[ordered]@{opened='FAIL';error=$_.Exception.Message} } finally { if ($word) { $word.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } } }
$rec.pdf=[ordered]@{file='Study.pdf';bytes=(Get-Item (Join-Path $ReportDir 'Study.pdf')).Length;header=[Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes((Join-Path $ReportDir 'Study.pdf'))[0..7])}
$json=$rec | ConvertTo-Json -Depth 6
$json | Out-File -Encoding utf8 (Join-Path $OutDir ('OFFICE_CHECK_'+$Part+'.json')); $json
$st=if ($Part -eq 'Excel') {$rec.excel.status} else {$rec.word.status}; if ($st -ne 'PASS') { exit 1 }
