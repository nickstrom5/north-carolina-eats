// North Carolina Eats brand: the app icon (Nick's pick 2026-10-26: concept C of scripts/icon-concepts.swift, a buttermilk biscuit, tall
// and whole with a golden-brown domed top and pale flaky sides, on flag red; the shared Eats Ranked icon style, state-prompts/ICON-STYLE.md,
// no backing shape).
// Usage, from nc-eats/: swift scripts/make-brand.swift   -> NorthCarolinaEats/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png,
// docs/ favicons and touch icons, docs/og.png. scripts/make-site.py draws the same mark as its inline SVG: change both together.
import AppKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

func rgb(_ hex: UInt32) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 255) / 255, green: CGFloat((hex >> 8) & 255) / 255, blue: CGFloat(hex & 255) / 255, alpha: 1)
}
let NAVY: UInt32 = 0x13294B, RED: UInt32 = 0xB31942

/// The buttermilk biscuit (front elevation): tall and whole, a golden-brown domed top (the up-facing plane is the darker one here,
// as on a real biscuit), pale flaky sides with two layer lines, a golden baked bottom. Tones: sides #F3D9A6, top and bottom #D69443,
// layers #E4B871.
func biscuit(_ c: CGContext, _ s: CGFloat) {
    func R(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect { CGRect(x: x * s, y: y * s, width: w * s, height: h * s) }
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: y * s) }
    let body = CGMutablePath()
    body.move(to: P(0.15, 0.36))
    body.addQuadCurve(to: P(0.23, 0.28), control: P(0.15, 0.28))
    body.addLine(to: P(0.77, 0.28))
    body.addQuadCurve(to: P(0.85, 0.36), control: P(0.85, 0.28))
    body.addLine(to: P(0.85, 0.58))
    body.addCurve(to: P(0.50, 0.72), control1: P(0.85, 0.68), control2: P(0.70, 0.72))
    body.addCurve(to: P(0.15, 0.58), control1: P(0.30, 0.72), control2: P(0.15, 0.68))
    body.closeSubpath()
    c.setFillColor(rgb(0xF3D9A6)); c.addPath(body); c.fillPath()
    c.saveGState(); c.addPath(body); c.clip()
    c.setFillColor(rgb(0xD69443)); c.fill(R(0, 0, 1, 0.325))     // baked bottom
    c.setFillColor(rgb(0xD69443)); c.fill(R(0, 0.585, 1, 1))     // golden-brown top
    c.restoreGState()
    c.setStrokeColor(rgb(0xE4B871)); c.setLineWidth(0.036 * s); c.setLineCap(.round)
    for y in [0.415, 0.50] as [CGFloat] {
        c.move(to: P(0.22, y)); c.addLine(to: P(0.78, y)); c.strokePath()
    }
}

func render(_ n: Int, _ path: String, background: Bool) {
    let ctx = CGContext(data: nil, width: n, height: n, bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: background ? CGImageAlphaInfo.noneSkipLast.rawValue : CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.setShouldAntialias(true)
    if background { ctx.setFillColor(rgb(RED)); ctx.fill(CGRect(x: 0, y: 0, width: n, height: n)) }
    biscuit(ctx, CGFloat(n))
    let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: path) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(d, ctx.makeImage()!, nil)
    guard CGImageDestinationFinalize(d) else { fatalError("could not write \(path)") }
    print("wrote", path)
}
render(1024, "NorthCarolinaEats/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png", background: true)
try? FileManager.default.createDirectory(atPath: "docs", withIntermediateDirectories: true)
for (n, name) in [(512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (32, "favicon-32.png")] {
    render(n, "docs/" + name, background: true)
}

/// The share image (1200 x 630): flag navy, the biscuit on a red square at the left, the name and tagline at the right, and the
/// mountains-to-sea horizon from the app's Home screen along the bottom over a red rule.
func og(_ path: String) {
    let W = 1200, H = 630
    let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setShouldAntialias(true)
    ctx.setFillColor(rgb(NAVY)); ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
    // the horizon (CoreGraphics y-up): Blue Ridge ridges at the left easing into dunes at the right, over a red rule
    let Wf = CGFloat(W)
    for (pts, hex) in [([(0, 52.0), (60, 80.0), (115, 58.0), (170, 90.0), (230, 62.0), (290, 76.0), (350, 50.0), (420, 60.0), (520, 44.0),
                         (640, 50.0), (760, 36.0), (900, 40.0), (1040, 30.0), (1200, 34.0)], 0x5D7AA6 as UInt32),
                       ([(0, 40.0), (70, 64.0), (130, 44.0), (190, 70.0), (250, 46.0), (320, 56.0), (400, 38.0), (520, 38.0), (660, 32.0),
                         (820, 32.0), (980, 28.0), (1200, 28.0)], 0x2A4570),
                       ([(0, 26.0), (120, 40.0), (260, 30.0), (420, 26.0), (620, 24.0), (800, 24.0), (960, 20.0), (1060, 24.0), (1110, 20.0),
                         (1150, 24.0), (1200, 20.0)], 0x0B1A33)] as [([(CGFloat, CGFloat)], UInt32)] {
        let p = CGMutablePath(); p.move(to: CGPoint(x: 0, y: 0))
        for (x, y) in pts { p.addLine(to: CGPoint(x: x * Wf / 1200, y: y)) }
        p.addLine(to: CGPoint(x: Wf, y: 0)); p.closeSubpath()
        ctx.setFillColor(rgb(hex)); ctx.addPath(p); ctx.fillPath()
    }
    ctx.setFillColor(rgb(RED)); ctx.fill(CGRect(x: 0, y: 0, width: W, height: 8))
    // the app icon's red square with the biscuit
    let sq = CGRect(x: 70, y: 150, width: 400, height: 400)
    ctx.saveGState(); ctx.addPath(CGPath(roundedRect: sq, cornerWidth: 88, cornerHeight: 88, transform: nil)); ctx.clip()
    ctx.setFillColor(rgb(RED)); ctx.fill(sq)
    ctx.translateBy(x: sq.minX, y: sq.minY); biscuit(ctx, 400)
    ctx.restoreGState()
    let ns = NSGraphicsContext(cgContext: ctx, flipped: false)
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = ns
    let title = NSFont(name: "AvenirNextCondensed-Heavy", size: 88) ?? NSFont.boldSystemFont(ofSize: 80)
    let sub = NSFont(name: "AvenirNextCondensed-DemiBold", size: 38) ?? NSFont.boldSystemFont(ofSize: 34)
    NSAttributedString(string: "NORTH CAROLINA", attributes: [.font: title, .foregroundColor: NSColor.white]).draw(at: NSPoint(x: 520, y: 398))
    NSAttributedString(string: "EATS", attributes: [.font: title, .foregroundColor: NSColor.white]).draw(at: NSPoint(x: 520, y: 300))
    NSAttributedString(string: "RESTAURANTS, BBQ & BISCUITS", attributes: [.font: sub, .foregroundColor: NSColor(srgbRed: 0.965, green: 0.867, blue: 0.890, alpha: 1)]).draw(at: NSPoint(x: 524, y: 240))
    NSGraphicsContext.restoreGraphicsState()
    let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: path) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(d, ctx.makeImage()!, nil)
    guard CGImageDestinationFinalize(d) else { fatalError("could not write \(path)") }
    print("wrote", path)
}
og("docs/og.png")
