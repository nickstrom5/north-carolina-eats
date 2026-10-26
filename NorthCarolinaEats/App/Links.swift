import Foundation

/// The app's web pages and support address, in one place.
/// The site is GitHub Pages at the project address until northcarolina.eatsranked.com resolves (Nick adds a Cloudflare CNAME
/// northcarolina -> nickstrom5.github.io, DNS only; then scripts/make-site.py sets CUSTOM_DOMAIN). GitHub forwards these github.io
/// links to the custom domain after the switch, so a shipped build keeps working; point them at the new domain in the next update.
enum Links {
    static let site = URL(string: "https://nickstrom5.github.io/north-carolina-eats/")!
    /// The app's data updates: scripts/publish_app_data.py writes docs/data/app/ (OTA-DATA.md).
    static let appData = URL(string: site.absoluteString + "data/app/")!
    static let privacy = URL(string: site.absoluteString + "privacy.html")!
    static let terms = URL(string: site.absoluteString + "terms.html")!
    /// Wake County's food inspections on its open data hub (CC BY 4.0)
    static let wakeInspections = URL(string: "https://data.wake.gov/datasets/ebe3ae7f76954fad81411612d7c4fb17")!
    /// Wake County's permitted food facilities on its open data hub
    static let wakePermits = URL(string: "https://data.wake.gov/datasets/124c2187da8c41c59bde04fa67eb2872")!
    /// the state's inspection search (NC DHHS, all counties); opened, never scraped. A county's page is this + its number.
    static let inspections = URL(string: "https://public.cdpehs.com/NCENVPBL/ESTABLISHMENT/ShowESTABLISHMENTTablePage.aspx")!
    /// the grading rule, 15A NCAC 18A .2600 (NC DHHS Environmental Health)
    static let gradingRules = URL(string: "https://ehs.dph.ncdhhs.gov/docs/rules/Sanitation-of-FoodEstablishments-15ANCAC18A-2600.pdf")!
    static let supportEmail = "nick@eatsranked.com"

    static var correctionEmail: URL {
        URL(string: "mailto:\(supportEmail)?subject=North%20Carolina%20Eats%20correction")!
    }

    // MARK: Share

    /// The web app. It opens a place's panel from the hash, explore/#p=<id> (readHash in scripts/explore.js), using the app's ids.
    static let explore = URL(string: site.absoluteString + "explore/")!

    /// What Share sends: the place's own page in the web app, never an Apple Maps or Google link (Apple Maps has its own button).
    /// The id is escaped the way the page's encodeURIComponent would escape it. The web app lists every place
    /// the app does (a unit test checks the ids against docs/data).
    /// The web app lists restaurants only: the venues the app hides by default (stadium stands, gas-station counters) aren't there.
    static func onWeb(_ place: Place) -> Bool { !place.isVenue }
    static func share(_ place: Place) -> URL {
        guard onWeb(place), let id = place.id.addingPercentEncoding(withAllowedCharacters: uriComponent),
              let url = URL(string: explore.absoluteString + "#p=" + id) else { return explore }
        return url
    }

    /// The text that goes with the link: the place, its town and the app. No street address, which Messages turns into a Maps link.
    static func shareMessage(_ place: Place) -> String {
        [place.name, place.city ?? ""].filter { !$0.isEmpty }.joined(separator: ", ") + ", on North Carolina Eats"
    }

    /// What encodeURIComponent leaves as is.
    private static let uriComponent = CharacterSet(charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!~*'()")
}
