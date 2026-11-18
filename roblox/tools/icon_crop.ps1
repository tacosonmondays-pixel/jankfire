# Cuts a square product icon out of a model render sheet (tools/blender/sheets: six panels under a title line; the
# top-left panel is the 3/4 view). Panel 1 spans x 4..644, y 30..450; the square is centred on the panel and scaled to
# 512 x 512. No text: the sheet's title line is above the crop. Usage:
#   powershell -File icon_crop.ps1 <sheet.jpg> <out.png> [panel 1-6]
param([string]$sheet, [string]$out, [int]$panel = 1)
Add-Type -AssemblyName System.Drawing
$src = [System.Drawing.Image]::FromFile($sheet)
$col = ($panel - 1) % 3
$row = [math]::Floor(($panel - 1) / 3)
$px = 4 + $col * 644
$py = 30 + $row * 425
$cx = $px + 320
$size = 420
$sx = $cx - 210
$rect = New-Object System.Drawing.Rectangle $sx, $py, $size, $size
$bmp = New-Object System.Drawing.Bitmap 512, 512
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($src, (New-Object System.Drawing.Rectangle 0, 0, 512, 512), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $src.Dispose()
Write-Output "wrote $out"
