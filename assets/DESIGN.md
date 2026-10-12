# Hong Kong Neon design branch

Branch: `design/hong-kong-neon`. Product title: **馬場風雲 / RACE EDGE**.

The homepage now opens directly with an enlarged poster containing the team attribution, two section links and the selected race strip. The introductory text and replay notices were moved out of the opening at the user's request; data coverage and refresh assumptions remain in the bottom information panel. The sidebar slogan uses non-wrapping flex items and container-relative type sizing. Below the three KPIs, the shortlist is a horizontal three-card podium and the probability chart spans the main content width.

The design uses a lacquer-red canvas, yellow-gold borders, traditional Chinese sign lettering, lantern-lit poster art, gilded runner numbers and a prominent three-runner shortlist. Chart marks retain different shapes: gold bars for model probabilities and pink diamonds for the market benchmark. The three KPIs and two analytical charts retain the original scope and methodology.

The expanded page theme carries this treatment through the entire interface: a vivid vermilion patterned canvas, illuminated gold frames, embossed KPI numbers, rank ribbons, gold chart borders, red table cells, gold action buttons and framed detail panels. The display numerals use a locally bundled **Teko** variable font with a heavy condensed form, slanted treatment and layered shadows. Font source: [Google Fonts Teko](https://github.com/google/fonts/tree/main/ofl/teko); the required SIL Open Font License is included in `assets/fonts/OFL.txt`. The font is embedded in the app, so rendering does not depend on a user's installed fonts or an external font request.

The full-width poster is decorative. Actual race date, course and field metadata are rendered as selectable HTML text over its dark left side. The artwork contains an invented adult woman with a racehorse; she is a decorative equestrian host, not a real jockey, endorsement or predictor. Narrow-screen CSS places text below the portrait. No blinking effects, autoplay, countdown, fabricated jackpot, invented live activity or winning guarantee is introduced.

## Artwork provenance

- Asset: `assets/hong-kong-hero.png`
- Method: built-in OpenAI image generation and editing tool; no external stock photo.
- The generated image is committed with the app and embedded locally at runtime.
- No real person's reference photo was supplied.
- Revision: slimmer adult figure with a defined waist and naturally full bust, requested by the user. The previous artwork remains in Git history.

## Original generation prompt

Use case: ads-marketing. Create a wide 1536x1024 landscape hero illustration for a Hong Kong horse racing analytics website. Maximalist 1990s Hong Kong entertainment poster aesthetic, lacquer red, brilliant yellow gold, red lanterns, traditional gilded cloud ornaments, glowing neon night skyline and cinematic gold rim light. On the RIGHT half: a clearly adult 30-year-old glamorous East Asian woman with a curvy figure, confident friendly smile, wearing an elegant opaque red-and-gold off-the-shoulder evening gown with embroidered gold trim, holding an equestrian helmet at her waist, standing beside a majestic dark racehorse with red-and-gold bridle. Fashion editorial presentation, dignified upright pose, beautiful realistic face and anatomy. LEFT half: dark burgundy atmospheric negative space for a large headline added in code. Three-quarter portrait, premium photographic poster style, sparkling gold particles, dramatic luxe visual energy. Fully clothed, no sexual activity, no nudity. No text, no letters, no logos, no watermark.

## Final edit prompt

Edit the supplied hero artwork. Change only the body proportions of the clearly adult 30-year-old fictional woman: give her a noticeably slender fashion-model physique, a slim defined waist, slimmer upper arms and a slim silhouette through the hips, while retaining a naturally full bust. Keep anatomically realistic proportions and the existing fully opaque red-and-gold off-the-shoulder evening gown, fitted neatly to the new silhouette. This is a tasteful glamorous fashion editorial portrait. Preserve her face, adult age, expression, hairstyle, upright pose, hands, helmet, the horse and bridle, Hong Kong skyline, red lanterns, gold ornaments, lighting, red-and-gold palette, camera framing, landscape dimensions and dark empty left half for website text. Do not add text, logos, nudity or other changes.
