"""Reference sheets from LeyendasCuadrantes2027.xlsx (presentation only).

The payload is a lossless snapshot of cell values, style components and dimensions.
Source SHA256: afa83b6a59c89ca14f5d4209ed685e2afca9bf9a0b12afbd894fc4cfb60d3581.
No data from this reference enters the scheduler.
"""
from base64 import b64decode
import json
from zlib import decompress
from openpyxl.styles import Font, PatternFill, Border, Alignment
from openpyxl.xml.functions import fromstring

_REFERENCE = "eNrdWltu4zYU3YqgrymgifUWbaQBEjmatshjkBrzk8wHIzOxBrJoyHKmmUEW0wX0o+gSsrFe0ozetiVnbKVNAli85LnnvshLO/4uz5PHkMzlwfW1qpR+PyvXmqKLkVYj01OZkY4yma3YiubwoVEDzmSmYipanw/NVGgxrK5WpJaiayWho2hI0eySFAGDVmLqw7xRtkgFnXULq7arjAW4SmKt1lFd0Sz2V1ZsCxsLS1msiuZrhuIoNUqRUuE3lb7Sr6FX2V9VrNWIwVI+UxUbbKYktsEGzahKwRKt7BwDW6UK0tM6eZF9VuQZjhNeh/LhHY2So8MIT4n0gMOfb2QXh8FtHNzIvaPDOzwNwkcxoXORT0MaS8mETAnINC6bfxNLNDH22bSQTYOIxlzc41yy0p709kV/zoT4/hYknvjp3g6V/+zHjrfC3HeB2C4yo7dRAqiryKP9BN5y9kSclZTaVUntirn1saJ2tp3VN3Kg7SkCttZNBDouObejgG9d7HDBAO4gDI8OZzhJSBx5MODzTMgtK89K4nn0OGNXiPsYP2q6JbQ2Rc1pGIxvZPDt3i24YpqO7prLWK+e6uU0/xBaz3NcpNbS5vbRDmhdxz3dO+2aIO/W27RM90nr2qdeB0Feat87raqeqF4nldyFt8sw7532dKj2hx2UlINQB7l1VEM93j+t6/b7HRwXpmmZ9vHeaZHKfjvYQKcnfXcrWn55uKXxmMRHhyG5S2BhHNxP2GtCZ0wjTRI6hYdxgO9phPnNQiCY1XmwxD9dA+JkEkTMUn9l82fLC1QtsLB6H3a1QPH1r3CjBWoJeI3bQTQmf5AxyO2NyZiScbCYrsNu9qKK2caHsiU13aM2eU1wNelrAqtzvQmuhfu9/10trg6QqopO0TKPGa5VHjNYuzxmuNdvxfSY9vqnQ6vdybjNVqzj2++B0sKH3hu0aTdx7TU7fOuaegvbcqgfsXEbRLjXeFu91rjNLr8Z47avzF3ehXZm1du52qzA4EVC008DN3fP7m5Ar3e1inmdu70dbtIWqMY3nv/AwblF5nq7PwBeU09v5y3Eun3foD2sg++lLWxKNH8zj8PgPpqSCDCMOR1KDyROAp//D8GHMeH/RCgumdA4+EajhC9i9Ddya9jLoq2BsIh9P2I+IYR9QeK7fEYeSTTG7DGmX/l3Jq5ToaIxr3+hMY4DKp29l34riT4FJI7IvCT9/fnPWzymQnpBEwwrdOAF1efHIGbf25CdgapK7yXNgleY7udlZiaLFmEoZs/x8984ArMMoQtUcQokYHZOFaqqX6NqBKp0NsGpAafrOV11wpyyEYYSkTKzNFBmpDbgoosvsrUuAldMxgvfD57/iaQvNI7wGDAZhV6mMAZGhSIna0qhpxQfgcHkzqu5pEiPyyizYKj5CJUXWWKM6iO2iCMqfcRQxKxOBKUHlNZ2+fRoPMV+QKNMGcuCzW0zRDzsXIzqhWo1OcJWSLBxYKhsV+H5gTQkUk4DdxlW6AKva+yVRNID9rlVZM6mfTqdQfBJnNWdp6dWMkMYthDWWmErK21hklo1qWoPj6jmFGJb9ySPSEiSGN/iL7SIRa2w0uWM2YJD6d0MTpyAnVLMCfZprB8ki3HPp9FdIHL7Uxq2IUStv5lpSOY+juZZhX2CcKmbcZ/SGKVIF5DaZqQLISXRvFiKJ4DVN2NP8BcsnWFoODhMsXBc6sZm7EcST4M5ld7hxZxEfoCzWH0ADeZmDR8WcIoFWBo+/1W1gumwWuqANJbjrym6vVmLR+ZJ8EAliOUigiY3xmOJShd4WSk5XU5zXWfUF1Dofl+DcTLh3e9EHujGgWWZNnIsBZI80FE2HMoDzTgwTc1UbR3Gp/LARgcI2Y4G80+KPCHs/sA16bDWOlAV2J3pk5Y+ZbNW+mSnTyh96i+fnkC36MFXl6Pj0eXVr5crOrRV6tBDIRJd18q2pl3TdFF2dFydHp9JpbbIcU4D3BW5W5D4W/Es4ItEI9CNeiBvnQUUTxtfDnxOPeqC+hOSbxvmKhurfeF8zWoXrkuESjP2BVDOVrlxDLdAS0M6DaL77BQ697bRIko51XLVRkk5QfKVtw28YsRIaKlLc0VLIdnyaNgaW4nkyGuvo+zChVBRV3MVFcXKuxi2xlZcuPDa6yi5UO7aqGGHRjvpxqhB50WNuixq2FFRw+6J1nfKQndCW3YitNeuk3UYZ3U3UWQ97T+68dJhnp7+BXHsVGE="


def install_legend(wb, rotatorio: bool) -> None:
    data = json.loads(decompress(b64decode(_REFERENCE)))
    title = "LeyendaROTATORIO" if rotatorio else "Leyenda"
    index = min((wb.index(wb[name]) for name in ("Leyenda", "LeyendaROTATORIO") if name in wb.sheetnames), default=len(wb.sheetnames))
    for name in ("Leyenda", "LeyendaROTATORIO"):
        if name in wb.sheetnames:
            del wb[name]
    ws = wb.create_sheet(title, index)
    reference = data["sheets"][title]
    fonts, fills, borders, alignments = [
        [cls.from_tree(fromstring(xml)) for xml in parts]
        for cls, parts in zip((Font, PatternFill, Border, Alignment), data["parts"])
    ]
    for r, row in enumerate(reference["rows"], 1):
        for c, (value, style_id) in enumerate(row, 1):
            cell = ws.cell(r, c, value)
            font, fill, border, _, _, alignment, *_ = data["styles"][style_id]
            cell.font = fonts[font]
            cell.fill = fills[fill]
            cell.border = borders[border]
            cell.alignment = alignments[alignment]
    ws.sheet_format.baseColWidth = 10
    ws.sheet_format.defaultColWidth = 9.109375
    ws.sheet_format.defaultRowHeight = 14.4
    for col, width in reference["widths"].items():
        ws.column_dimensions[col].width = width
    for row, height in reference["heights"].items():
        ws.row_dimensions[int(row)].height = height
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = ws.sheet_view.zoomScaleNormal = 85
    ws.page_margins.top = ws.page_margins.bottom = 1.0
