// North Carolina icon concepts for Nick's pick, in the shared Eats Ranked icon style (state-prompts/ICON-STYLE.md v1):
// one flat, level, centred food on a plain background; no scenery, tilt, texture, gloss or gradients.
// Usage (from nc-eats/): swift scripts/icon-concepts.swift   -> playbook/brand/concept-{a,b,c}-1024.png and -512, -180, -60 copies
//   A  barbecue sandwich with slaw (chopped pork, slaw on top, a soft bun), on longleaf pine (the landscape palette)
//   B  sweet potato, the state vegetable, its cut end showing the orange flesh, on flag navy
//   C  buttermilk biscuit, tall and whole with a golden-brown top and flaky sides, on flag red
// Palettes (the prompt's): flag navy #13294B and red #B31942; landscape longleaf pine #2F5D3A. Food tones are listed per concept.
import AppKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

func rgb(_ hex: UInt32) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 255) / 255, green: CGFloat((hex >> 8) & 255) / 255, blue: CGFloat(hex & 255) / 255, alpha: 1)
}
let NAVY: UInt32 = 0x13294B, RED: UInt32 = 0xB31942, PINE: UInt32 = 0x2F5D3A

// MARK: A, barbecue sandwich (side elevation, CoreGraphics y-up): a flat soft bun, a deep layer of chopped pork with a few lighter
// strands, a thick band of slaw, a low domed top bun with a lighter cap. 0.72 wide. Tones: bun #E3A34E, bun top #EEC27A (also the
// strands), pork #8E4426, slaw #E2EBBE.
func bbqSandwich(_ c: CGContext, _ s: CGFloat) {
    let dn: CGFloat = 0.02
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: (y - dn) * s) }
    func R(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect { CGRect(x: x * s, y: (y - dn) * s, width: w * s, height: h * s) }
    // bottom bun
    c.setFillColor(rgb(0xE3A34E))
    c.addPath(CGPath(roundedRect: R(0.17, 0.28, 0.66, 0.085), cornerWidth: 0.04 * s, cornerHeight: 0.04 * s, transform: nil)); c.fillPath()
    // chopped pork: a deep heap that bulges past the bun at both ends
    let pork = CGMutablePath()
    pork.move(to: P(0.20, 0.345))
    pork.addLine(to: P(0.80, 0.345))
    pork.addCurve(to: P(0.80, 0.505), control1: P(0.89, 0.345), control2: P(0.89, 0.505))
    pork.addLine(to: P(0.20, 0.505))
    pork.addCurve(to: P(0.20, 0.345), control1: P(0.11, 0.505), control2: P(0.11, 0.345))
    pork.closeSubpath()
    c.setFillColor(rgb(0x8E4426)); c.addPath(pork); c.fillPath()
    // pulled strands: short round-cap strokes in the bun-top tone
    c.setStrokeColor(rgb(0xEEC27A)); c.setLineWidth(0.034 * s); c.setLineCap(.round)
    for (x0, y0, x1, y1) in [(0.22, 0.41, 0.30, 0.43), (0.40, 0.395, 0.48, 0.38), (0.57, 0.425, 0.65, 0.41), (0.72, 0.39, 0.79, 0.405)] as [(CGFloat, CGFloat, CGFloat, CGFloat)] {
        c.move(to: P(x0, y0)); c.addLine(to: P(x1, y1)); c.strokePath()
    }
    // slaw: a thick pale band with a waved lower edge over the pork, reaching past the bun at both ends
    let slaw = CGMutablePath()
    slaw.move(to: P(0.15, 0.575))
    slaw.addLine(to: P(0.85, 0.575))
    slaw.addLine(to: P(0.85, 0.52))
    slaw.addCurve(to: P(0.50, 0.49), control1: P(0.74, 0.47), control2: P(0.62, 0.52))
    slaw.addCurve(to: P(0.15, 0.52), control1: P(0.38, 0.465), control2: P(0.26, 0.52))
    slaw.closeSubpath()
    c.setFillColor(rgb(0xE2EBBE)); c.addPath(slaw); c.fillPath()
    // top bun: a low dome with a lighter cap (hard edge)
    let dome = CGMutablePath()
    dome.move(to: P(0.17, 0.565))
    dome.addLine(to: P(0.83, 0.565))
    dome.addCurve(to: P(0.50, 0.735), control1: P(0.83, 0.67), control2: P(0.71, 0.735))
    dome.addCurve(to: P(0.17, 0.565), control1: P(0.29, 0.735), control2: P(0.17, 0.67))
    dome.closeSubpath()
    c.setFillColor(rgb(0xE3A34E)); c.addPath(dome); c.fillPath()
    c.saveGState(); c.addPath(dome); c.clip()
    c.setFillColor(rgb(0xEEC27A)); c.fill(R(0, 0.665, 1, 1))
    c.restoreGState()
}

// MARK: B, sweet potato (long food: side elevation), fat in the middle and tapering to a root tip at the left; the right end is cut, and
// the cut face shows the orange flesh. 0.72 long, 0.37 tall. Tones: skin #A8492C, lighter top plane #C25E39, flesh #E8914F, eyes #7E3520.
func sweetPotato(_ c: CGContext, _ s: CGFloat) {
    func P(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: x * s, y: y * s) }
    let body = CGMutablePath()
    body.move(to: P(0.14, 0.495))
    body.addCurve(to: P(0.44, 0.675), control1: P(0.20, 0.60), control2: P(0.31, 0.675))
    body.addCurve(to: P(0.80, 0.645), control1: P(0.60, 0.675), control2: P(0.72, 0.665))
    body.addLine(to: P(0.80, 0.345))
    body.addCurve(to: P(0.44, 0.305), control1: P(0.72, 0.320), control2: P(0.60, 0.305))
    body.addCurve(to: P(0.14, 0.495), control1: P(0.31, 0.305), control2: P(0.20, 0.39))
    body.closeSubpath()
    c.setFillColor(rgb(0xA8492C)); c.addPath(body); c.fillPath()
    c.saveGState(); c.addPath(body); c.clip()
    c.setFillColor(rgb(0xC25E39)); c.fill(CGRect(x: 0, y: 0.555 * s, width: s, height: s))
    c.restoreGState()
    // the cut face at the right end
    c.setFillColor(rgb(0xE8914F))
    c.fillEllipse(in: CGRect(x: 0.735 * s, y: 0.345 * s, width: 0.125 * s, height: 0.30 * s))
    // three eyes on the skin: short round-cap strokes in the darker tone
    c.setStrokeColor(rgb(0x7E3520)); c.setLineWidth(0.034 * s); c.setLineCap(.round)
    for (x, y) in [(0.32, 0.45), (0.47, 0.60), (0.58, 0.41)] as [(CGFloat, CGFloat)] {
        c.move(to: P(x - 0.025, y)); c.addLine(to: P(x + 0.025, y)); c.strokePath()
    }
}

// MARK: C, buttermilk biscuit (front elevation): tall and whole, a golden-brown domed top (the up-facing plane is the darker one here,
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

// MARK: - main
let root = URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent().deletingLastPathComponent().path
let out = root + "/playbook/brand"
try? FileManager.default.createDirectory(atPath: out, withIntermediateDirectories: true)
func canvas(_ n: Int) -> CGContext {
    let c = CGContext(data: nil, width: n, height: n, bitsPerComponent: 8, bytesPerRow: 0,
                      space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    c.setAllowsAntialiasing(true); c.setShouldAntialias(true); c.interpolationQuality = .high
    return c
}
func save(_ img: CGImage, _ name: String) {
    let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: out + "/" + name) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, img, nil)
    guard CGImageDestinationFinalize(dest) else { fatalError("could not write \(name)") }
}
for (key, bg, draw) in [("a", PINE, bbqSandwich), ("b", NAVY, sweetPotato), ("c", RED, biscuit)] as [(String, UInt32, (CGContext, CGFloat) -> Void)] {
    let c = canvas(1024)
    c.setFillColor(rgb(bg)); c.fill(CGRect(x: 0, y: 0, width: 1024, height: 1024))
    draw(c, 1024)
    let full = c.makeImage()!
    save(full, "concept-\(key)-1024.png")
    for n in [512, 180, 60] {
        let sm = canvas(n); sm.draw(full, in: CGRect(x: 0, y: 0, width: n, height: n)); save(sm.makeImage()!, "concept-\(key)-\(n).png")
    }
    print("wrote concept-\(key)")
}
