import SwiftUI
import UIKit
import CoreText

/// North Carolina flag palette (Nick's pick, 2026-10-26), light only: flag navy #13294B (14.5:1 on white) for titles, tint and accents;
/// flag red #B31942 (6.7:1 on white, white on it 6.7:1) for the hand-checked North Carolina guide cards under white text and for
/// MICHELIN chips; biscuit gold #E9A23B only as a pin and card fill under dark text (never text). No team colors (UNC, NC State, Duke,
/// Wake Forest). The names `green`/`gold` are kept from Wisconsin Eats so the shared views read the same; here `green` is the flag
/// navy and `gold` the flag red.
enum Theme {
    static let green = Color(hex: 0x13294B)      // flag navy: titles, tint, primary text accents
    static let green2 = Color(hex: 0x2A4570)
    static let gold = Color(hex: 0xB31942)       // flag red: card fills under white text, chips
    static let goldSoft = Color(hex: 0xF6DDE3)   // soft red
    static let lime = Color(hex: 0xE9A23B)       // biscuit gold, fills only (hand-checked pins), under dark text
    static let limeSoft = Color(hex: 0xFBEACB)
    static let sand = Color(hex: 0xF4F6F9)       // the Home background, a cool off-white
    static let red = Color(hex: 0xB31942)        // MICHELIN chips
    static let ink = Color(hex: 0x0E1A2E)
    static let ink2 = Color(hex: 0x26364F)
    static let muted = Color(hex: 0x556178)
    static let surface = Color.white
    static let surface2 = Color(hex: 0xF2F4F8)
    static let surface3 = Color(hex: 0xE1E6EF)
    static let rule = Color(hex: 0xDCE2EC)
    static let rule2 = Color(hex: 0xB5C0D3)
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
    }
}

/// A small uppercase label: "STONE CRAB", "1 MICHELIN STAR".
struct Chip: View {
    enum Style { case gold, green, red, plain, dashed }
    let text: String
    var style: Style = .plain

    var body: some View {
        Text(text.uppercased())
            .font(.caption2.weight(.bold))
            .tracking(0.4)
            .padding(.horizontal, 7).padding(.vertical, 3)
            .foregroundStyle(style == .green || style == .red ? Color.white : style == .dashed ? Theme.muted : style == .gold ? Theme.ink : Theme.green)
            .background {
                RoundedRectangle(cornerRadius: 5).fill(style == .gold ? Theme.goldSoft : style == .green ? Theme.green : style == .red ? Theme.red
                                                       : style == .dashed ? .clear : Theme.surface2)
            }
            .overlay {
                if style == .dashed { RoundedRectangle(cornerRadius: 5).strokeBorder(Theme.rule2, style: StrokeStyle(lineWidth: 1, dash: [3, 2])) }
            }
            .accessibilityLabel(text)
    }
}

/// North Carolina Eats' lettering: the system face drawn compressed and heavy for titles and guide names (like a show poster), and the
/// system monospaced face for numbers, dates and small labels. No bundled fonts.
struct DisplayFont: ViewModifier {
    let size: CGFloat
    var weight: Font.Weight = .black
    @ScaledMetric(relativeTo: .body) private var scale: CGFloat = 1

    func body(content: Content) -> some View {
        content.font(.system(size: size * min(scale, 1.6), weight: weight).width(.compressed))
    }
}

/// Numbers, dates and small labels in the system monospaced face, scaled like DisplayFont.
struct MonoFont: ViewModifier {
    let size: CGFloat
    var weight: Font.Weight = .semibold
    @ScaledMetric(relativeTo: .body) private var scale: CGFloat = 1

    func body(content: Content) -> some View {
        content.font(.system(size: size * min(scale, 1.6), weight: weight, design: .monospaced))
    }
}

extension View {
    func displayFont(_ size: CGFloat, weight: Font.Weight = .black) -> some View {
        modifier(DisplayFont(size: size, weight: weight))
    }

    func monoFont(_ size: CGFloat, weight: Font.Weight = .semibold) -> some View {
        modifier(MonoFont(size: size, weight: weight))
    }
}

/// The band under the Home title: mountains to sea. Blue Ridge ridges in the west ease into Piedmont hills and the Outer Banks' low
/// dunes, in navy tones over a thin red rule (the leaderboard's header draws the same horizon).
struct Stripes: View {
    var height: CGFloat = 6

    var body: some View {
        Canvas { ctx, size in
            let w = size.width, h = size.height, rule = max(2, h * 0.1)
            ctx.fill(Path(CGRect(x: 0, y: 0, width: w, height: rule)), with: .color(Theme.red))
            // each layer: (x, height above the bottom) as fractions, west to east; the back layer is the highest and lightest
            let layers: [([(CGFloat, CGFloat)], Color)] = [
                ([(0, 0.46), (0.05, 0.77), (0.096, 0.50), (0.142, 0.88), (0.19, 0.54), (0.24, 0.73), (0.29, 0.42), (0.35, 0.54),
                  (0.43, 0.35), (0.53, 0.42), (0.63, 0.27), (0.75, 0.31), (0.87, 0.19), (1, 0.23)], Color(hex: 0x5D7AA6)),
                ([(0, 0.31), (0.058, 0.58), (0.108, 0.35), (0.158, 0.65), (0.21, 0.38), (0.27, 0.50), (0.33, 0.27), (0.43, 0.27),
                  (0.55, 0.19), (0.68, 0.19), (0.82, 0.15), (1, 0.15)], Theme.green2),
                ([(0, 0.15), (0.1, 0.31), (0.22, 0.19), (0.35, 0.15), (0.52, 0.12), (0.67, 0.12), (0.8, 0.08), (0.88, 0.12),
                  (0.92, 0.08), (0.96, 0.12), (1, 0.08)], Theme.green),
            ]
            for (pts, color) in layers {
                var p = Path()
                p.move(to: CGPoint(x: 0, y: h))
                for (x, y) in pts { p.addLine(to: CGPoint(x: x * w, y: h - y * (h - rule))) }
                p.addLine(to: CGPoint(x: w, y: h))
                p.closeSubpath()
                ctx.fill(p, with: .color(color))
            }
        }
        .frame(height: height * 4)
        .accessibilityHidden(true)
    }
}

extension View {
    /// An inline navigation title in the display type. UINavigationBar.appearance() didn't reach every SwiftUI bar on iOS 27
    /// (the Map title went from compressed blue to plain black after a push and pop; place titles were always plain), so the
    /// title is our own view in the bar. The navigation title is still set, for the back button and VoiceOver.
    func inlineTitle(_ title: String) -> some View {
        navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text(title).displayFont(19, weight: .heavy).foregroundStyle(Theme.green)
                        .lineLimit(1).minimumScaleFactor(0.7)
                        .accessibilityAddTraits(.isHeader)
                }
            }
    }
}
