import SwiftUI

struct AboutView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Text("NORTH CAROLINA EATS").displayFont(32).foregroundStyle(Theme.green)
                    Text("A free guide to \(model.restaurantCount.formatted()) North Carolina restaurants, with MICHELIN and James Beard honors, Wake County's official inspection scores, and hand-checked lists of North Carolina's own food. No account, no ads, no tracking.")
                        .font(.subheadline).foregroundStyle(Theme.ink2)
                    Text("North Carolina Eats is an independent app by Nicholas Soderstrom. It is not affiliated with, endorsed by or operated by the State of North Carolina, the NC Department of Health and Human Services, Wake County or any county health department, the NC ABC Commission, VisitNC, the MICHELIN Guide, the James Beard Foundation, Apple, or any restaurant or chain. Other names are trademarks of their owners.")
                        .font(.footnote).foregroundStyle(Theme.muted)
                }
                .padding(.vertical, 4)
            }
            Section("How the lists are built") {
                Text("Hand-checked lists (Eastern whole hog, Lexington barbecue, Carolina hot dogs, Calabash seafood, biscuits and livermush) include only places named for that food by a source and shown to be operating in 2025 or 2026: the MICHELIN Guide, a Wake County inspection, the place's own website, dated local press, or a current listing by the state's or the town's tourism office. Addresses are checked against the map data. Founding years mean the year it opened at this address.")
                Text("Honors are the MICHELIN Guide American South's 2026 North Carolina selection (a one-star restaurant, Bib Gourmands and recommended places), James Beard Foundation winners, the 2026 finalists and semifinalists, and America's Classics.")
                Text("North Carolina publishes no statewide list of its restaurants. This app starts from open map listings (Overture Maps) and keeps the kinds that proved reliable: checked against Wake County's permit list, which covers every place there that serves food, high-confidence listings matched a permit far more often than the kinds left out. Wake's permits also confirm Wake County places and add restaurants the map data missed. Adult clubs are left out. Website links are checked, and any that no longer belong to the place are left out.")
                Text("Every county inspects restaurants under the state's rules and posts a grade card by the door: the score and the grade it earns (A at 90 or more, B 80 to under 90, C 70 to under 80). Wake County publishes its inspections as data, so Wake places show the latest official score, the grade it earns, the date and the items cited. The other counties' reports are only in the state's search, linked from each place; no score is copied and no grade is computed.")
                Text("Ratings, reviews, hours and photos are Apple Maps' own, shown live in Apple's place card. This app doesn't store or rank by them.")
            }
            .font(.subheadline).foregroundStyle(Theme.ink2)
            Section("Sources") {
                source("Wake County Environmental Health & Safety", "Restaurants in Wake County, Food Inspections and Food Inspection Violations, Wake County Open Data (data.wake.gov), retrieved \(DayFormat.text(model.permitsUpdated) ?? model.permitsUpdated), inspections through \(DayFormat.text(model.inspectionsThrough) ?? model.inspectionsThrough). Licensed under CC BY 4.0 (creativecommons.org/licenses/by/4.0); filtered and matched to map listings for this app, and inspectors' names and comments left out. Wake County's notice: \u{201C}Wake County Geographic Information Services shall not be held liable for any errors in these data. This includes errors of omission, commission, errors concerning the content of the data, and relative and positional accuracy of the data. These data cannot be construed to be a legal document. Primary sources from which these data were compiled must be consulted for verification of information contained in these data.\u{201D}", Links.wakeInspections.absoluteString)
                source("NC Department of Health and Human Services", "The grading rule, 15A NCAC 18A .2662, and the state's inspection search for every county (public.cdpehs.com). Linked from each place; not copied.", Links.gradingRules.absoluteString)
                source("Overture Maps Foundation", "Restaurant listings and websites come from Overture Maps Foundation places data (overturemaps.org)\(model.overtureRelease.map { ", release \($0)" } ?? ""), filtered and reformatted for this app.\n• Data from Meta, Microsoft, DAC and BrightQuery. Available under CDLA Permissive 2.0.\n• Data from Foursquare. \(foursquareCopyright) Available under Apache 2.0. Foursquare data was transformed to the Overture schema; this app further filtered and reformatted it. See the NOTICE below.\n• Data from AllThePlaces. Available under CC0 1.0.\nResearched places are put on the map with Overture Maps addresses data (open address sources under permissive licenses, docs.overturemaps.org/attribution).", "https://overturemaps.org")
                source("Honors", "The MICHELIN Guide American South selection and James Beard Foundation awards, finalists, semifinalists and America's Classics are reported as facts and checked by hand against the official announcements. MICHELIN and the MICHELIN Guide are trademarks of Michelin. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. Other names belong to their owners.", "https://guide.michelin.com/us/en/north-carolina/restaurants")
                source("Maps", "Maps, place cards and directions by Apple Maps.", nil)
            }
            Section("Licenses") {
                NavigationLink("Community Data License Agreement – Permissive 2.0") { LicenseText(file: "CDLA-Permissive-2.0", title: "CDLA Permissive 2.0") }
                NavigationLink("Apache License 2.0") { LicenseText(file: "Apache-2.0", title: "Apache License 2.0") }
                NavigationLink("Foursquare OS Places NOTICE") { LicenseText(file: "Foursquare-NOTICE", title: "Foursquare NOTICE") }
            }
            Section("Privacy") {
                Text("The app collects nothing. Your location, if you allow it, only sorts lists by distance and shows where you are on the map, on this device. Saved places stay on this device.")
                    .font(.subheadline).foregroundStyle(Theme.ink2)
                DataUpdatesNote()
                    .font(.footnote).foregroundStyle(Theme.muted)
                Link("Privacy policy", destination: Links.privacy)
                Link("Terms of use", destination: Links.terms)
            }
            Section("Help") {
                Link("Report a missing or closed place", destination: Links.correctionEmail)
                Link("Email \(Links.supportEmail)", destination: URL(string: "mailto:\(Links.supportEmail)")!)
                Link("Website", destination: Links.site)
                Text("Data as of \(DayFormat.text(model.generated) ?? model.generated). Places open and close; check before you go. Version \(Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0")")
                    .font(.footnote).foregroundStyle(Theme.muted)
            }
        }
        .navigationTitle("About")
        .tint(Theme.green)
    }

    /// the copyright line exactly as the bundled Foursquare NOTICE has it, so the two can't disagree
    private var foursquareCopyright: String {
        guard let url = Bundle.main.url(forResource: "Foursquare-NOTICE", withExtension: "txt"),
              let text = try? String(contentsOf: url, encoding: .utf8),
              let line = text.split(separator: "\n").first(where: { $0.hasPrefix("©") }) else { return "© Foursquare Labs, Inc. All rights reserved." }
        return line.trimmingCharacters(in: .whitespaces)
    }

    @ViewBuilder
    private func source(_ name: String, _ detail: String, _ url: String?) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            if let url, let u = URL(string: url) { Link(name, destination: u).font(.subheadline.weight(.semibold)) }
            else { Text(name).font(.subheadline.weight(.semibold)) }
            Text(detail).font(.caption).foregroundStyle(Theme.muted)
        }
    }
}

/// A bundled license text (Resources/Licenses), reflowed rather than shown as raw 80-column lines.
struct LicenseText: View {
    let file: String
    let title: String

    var body: some View {
        ScrollView {
            Text(text).font(.footnote).foregroundStyle(Theme.ink).textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading).padding()
        }
        .inlineTitle(title)
    }

    private var text: String {
        guard let url = Bundle.main.url(forResource: file, withExtension: "txt"),
              let raw = try? String(contentsOf: url, encoding: .utf8) else { return "License text missing." }
        // join hard-wrapped lines into paragraphs; keep blank lines and list items as breaks
        var out: [String] = []
        for para in raw.components(separatedBy: "\n\n") {
            let lines = para.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespaces) }
            var joined = ""
            for l in lines where !l.isEmpty {
                let startsItem = l.hasPrefix("–") || l.hasPrefix("-") || l.range(of: #"^\(?[a-z0-9]{1,3}[.)]\s"#, options: .regularExpression) != nil
                joined += joined.isEmpty ? l : (startsItem ? "\n" + l : " " + l)
            }
            if !joined.isEmpty { out.append(joined) }
        }
        return out.joined(separator: "\n\n")
    }
}
