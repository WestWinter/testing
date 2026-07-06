#!/usr/bin/env python3
"""
US Government AI Equity-Stake Screen — scoring engine + Excel builder.

Scores every US-listed AI-exposed name on a 9-factor rubric reverse-engineered
from the administration's completed deals (Intel, MP Materials, Lithium
Americas, Trilogy, USA Rare Earth, Quantum-9, L3Harris, NVDA/AMD revenue
shares, US Steel golden share, Westinghouse). Emits gov_ai_stake_screen.xlsx
and markdown table fragments for REPORT.md.

Data vintage: 2026-07-06. Market caps are approximate, web-sourced.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------- factors ---
# weight, short definition (full rubrics in the report)
FACTORS = {
    "hooks":  (20, "Federal leverage hooks", "Existing federal money or permission the govt can price: CHIPS/DoD/DOE grants+loans it can convert (Intel, LAC, quantum), export licenses (NVDA/AMD), permits (TMQ, TMC), merger approvals (X). 10 = live conversion/renegotiation lever; 0 = no federal surface."),
    "choke":  (18, "Strategic chokepoint", "Sole/scarce domestic source of an AI-stack or defense input (MP = only US RE mine; LEU = only US-owned enrichment; INTC = only US leading-edge logic). 10 = monopoly domestic chokepoint."),
    "need":   (14, "Capital need / wants something", "Distress, capex hunger, or a needed permission slip. The govt buys where it has leverage AND the company needs the deal (INTC, MP, LAC, USAR, WOLF). 10 = existential need."),
    "mech":   (10, "Mechanism feasibility", "US domicile/control, digestible size, an existing deal lane (conversion, warrant, unit-level equity, rev-share, golden share). ADRs and $1T+ caps get haircut; donation-model partially offsets for megacaps."),
    "align":  (10, "Political alignment / relationship", "CEO courtship, White House presence, pledges, rehabilitation arcs (Tan), Beijing-trip invites (Huang). Adversarial posture scores low."),
    "narr":   (10, "National-security narrative fit", "How cleanly a stake is sold as security policy + 'taxpayer upside'."),
    "china":  (8,  "China/adversary exposure leverage", "Export-control or supply-dependence leverage the govt can monetize (NVDA/AMD 15%->25% China rev shares; antimony/RE export bans)."),
    "build":  (6,  "Domestic buildout commitments", "Announced US capex the administration can attach itself to."),
    "signal": (4,  "Signal flow", "Already publicly floated: officials' statements, leaks, LOIs-in-discussion."),
}
# penalty: 0..-10 applied after weighted sum (exemption statements, short-seller
# clouds, prior exclusion, adversarial CEO)

W = {k: v[0] for k, v in FACTORS.items()}
ORDER = list(FACTORS.keys())

# --------------------------------------------------------------- universe ---
# (ticker, name, subsector, domicile, cap≈$B, status, scores..., penalty,
#  mechanism-if-it-happens, rationale)
# status: "" | "STAKED" | "STAKED-LOI" | "REV-SHARE" | "EXEMPTED"
# scores tuple order = ORDER
S = "Core AI compute & semis"
I = "AI infrastructure & power"
A = "AI software, hyperscale & defense AI"
M = "Strategic materials & frontier tech"

UNIVERSE = [
 # ---- Core AI compute & semis
 ("NVDA","NVIDIA",S,"US",4700,"REV-SHARE",(8,10,6,7,9,9,10,8,7),0,
  "Expanded export-license revenue share (15% H20 -> reported 25% H200); equity unlikely at $4.7T",
  "The permission-pricing template was invented for NVDA. Every China license cycle is a new event; Huang joined Trump's Beijing delegation May 2026 at the president's request. Too big to buy, perfectly sized to tax."),
 ("AMD","AMD",S,"US",380,"REV-SHARE",(7,8,6,7,8,8,9,7,5),0,
  "Rev-share expansion on MI-series China licenses; second-source compute champion",
  "Rides the same license lane as NVDA at a digestible size. Su has stayed aligned; MI308 rev-share already operating."),
 ("INTC","Intel",S,"US",490,"STAKED",(9,10,8,10,9,10,5,10,6),0,
  "Second tranche: 5% warrant @ $20 triggers if foundry control <51%; more Secure Enclave money",
  "The flagship precedent. Govt is up ~420% and politically invested in the turnaround; any foundry spin discussion mechanically creates the next event."),
 ("MU","Micron",S,"US",200,"EXEMPTED",(8,9,4,8,8,9,7,9,2),-8,
  "Stockpile/offtake-style support or Secure-Enclave-type award, not equity",
  "Only US memory/HBM maker - textbook chokepoint - but Commerce explicitly said it is NOT taking equity from recipients that raised US investment. The exemption is the tell: alignment bought immunity, not a stake."),
 ("AVGO","Broadcom",S,"US",1600,"",(3,8,2,5,6,6,6,5,2),0,"None visible; too healthy, no hooks",
  "Custom-silicon kingpin but no federal money to convert and no permission it needs."),
 ("QCOM","Qualcomm",S,"US",180,"",(4,7,4,6,6,6,8,5,2),0,"China-license rev share if handset/auto SoC controls tighten",
  "China revenue ~60%+; a license regime extension would put it in the NVDA lane overnight."),
 ("TXN","Texas Instruments",S,"US",170,"EXEMPTED",(6,6,2,7,6,6,5,7,2),-3,"None; finalized CHIPS, investing",
  "Finalized $1.6B CHIPS award and massive US fab buildout = good-behavior exemption."),
 ("ADI","Analog Devices",S,"US",120,"",(4,5,2,6,5,5,5,5,1),0,"None visible","No distress, modest hooks."),
 ("MRVL","Marvell",S,"US",70,"",(3,6,4,6,5,5,6,5,2),0,"None near-term","Custom AI silicon relevance, no federal hooks."),
 ("MCHP","Microchip",S,"US",35,"",(5,5,4,7,5,5,4,4,2),0,"CHIPS renegotiation if stress returns","Small CHIPS award; mature-node defense relevance."),
 ("ON","onsemi",S,"US",20,"",(4,5,4,6,4,4,4,4,1),0,"None near-term","SiC exposure but no live federal lever."),
 ("GFS","GlobalFoundries",S,"US",30,"STAKED-LOI",(9,8,6,8,7,8,6,7,6),0,
  "Equity already coming via $375M quantum-foundry LOI; further tranches vs Trusted Foundry/CHIPS $1.5B",
  "Already inside the tent (quantum-9). Mubadala control is the only wrinkle; US mature-node + trusted foundry status keeps the lane open."),
 ("WOLF","Wolfspeed",S,"US",2,"",(6,7,9,6,4,7,6,6,3),0,
  "Rescue equity in a CHIPS renegotiation post-Ch.11 - the Intel pattern at micro scale",
  "Distressed sole-ish US SiC platform; unfinalized CHIPS award is an open hook. Messy capital structure is the drag."),
 ("SKYT","SkyWater",S,"US",1.5,"",(8,7,7,5,5,8,4,5,4),0,
  "DoD trusted-foundry equity; complicated by pending IonQ acquisition",
  "US-owned trusted foundry, rad-hard; exactly the asset the state would anchor - but the IonQ deal muddies the entry point."),
 ("AMKR","Amkor",S,"US",10,"",(6,7,5,8,5,7,6,6,2),0,"CHIPS packaging award conversion/expansion",
  "Only US OSAT at scale; advanced packaging is the acknowledged CHIPS gap."),
 ("COHR","Coherent",S,"US",35,"",(5,7,5,7,5,6,6,5,2),0,"Photonics/defense award with equity kicker","Optics chokepoint-ish; some defense hooks."),
 ("LITE","Lumentum",S,"US",15,"",(5,7,5,7,5,6,6,5,2),0,"Same lane as COHR","Datacom photonics + defense photonics."),
 ("LRCX","Lam Research",S,"US",150,"",(3,9,2,6,5,6,9,5,2),0,"China-tool license rev-share (NVDA template applied to semicap)",
  "No subsidies to convert, but China tool sales under license = monetizable permission."),
 ("AMAT","Applied Materials",S,"US",180,"",(3,9,2,6,6,6,9,5,2),0,"Same license-pricing lane","Largest US semicap; same logic as LRCX."),
 ("KLAC","KLA",S,"US",140,"",(3,9,2,6,5,6,9,5,2),0,"Same license-pricing lane","Process-control monopoly-ish; China leverage."),
 ("TER","Teradyne",S,"US",20,"",(3,5,3,6,4,4,5,4,1),0,"None near-term","Test; limited hooks."),
 ("ENTG","Entegris",S,"US",15,"",(4,6,3,6,4,5,6,4,1),0,"Small CHIPS materials award exists","Materials purity chokepoint, modest."),
 ("ONTO","Onto Innovation",S,"US",10,"",(3,5,3,6,4,4,5,4,1),0,"None near-term","Metrology, small."),
 ("SNPS","Synopsys",S,"US",90,"",(4,8,3,6,5,5,9,4,2),0,"EDA China-license rev share",
  "EDA export controls were already weaponized in 2025; a license fee/rev-share is one memo away."),
 ("CDNS","Cadence",S,"US",90,"",(4,8,3,6,5,5,9,4,2),0,"Same as SNPS","EDA duopoly partner; same lane."),
 ("TSM","TSMC (ADR)",S,"Foreign (TW)",1500,"EXEMPTED",(6,10,3,2,7,8,8,9,3),-6,
  "Golden-share/JV-style condition on US fabs at most; equity ruled out by Commerce statement",
  "Ultimate chokepoint, wrong passport. Arizona buildout bought exemption; watch only for control-style conditions, not stakes."),
 ("ARM","Arm Holdings (ADR)",S,"Foreign (UK)",150,"",(3,7,2,3,6,5,5,4,2),0,"None plausible directly","SoftBank-controlled UK ADR; Stargate adjacency doesn't create a stake lane."),
 ("ASML","ASML (ADR)",S,"Foreign (NL)",400,"",(2,9,1,2,4,5,8,3,1),0,"None plausible","Dutch chokepoint; US leverage is export policy, not equity."),
 ("NXPI","NXP (ADR)",S,"Foreign (NL)",55,"",(3,6,2,3,4,4,6,4,1),0,"None plausible","Dutch domicile, no lane."),

 # ---- AI infrastructure & power
 ("CRWV","CoreWeave",I,"US",60,"",(5,6,8,7,7,6,2,9,5),0,
  "Federal AI-compute offtake or loan-guarantee package with warrants (MP-style price-floor analog for compute)",
  "Capital-hungry pure-play AI cloud; AI Action Plan contemplates federal compute procurement. A DOE/DoD anchor-tenant deal with warrants is the natural instrument."),
 ("NBIS","Nebius (ADR)",I,"Foreign (NL)",25,"",(4,5,7,4,5,4,2,7,3),0,"Unlikely; domicile","Foreign-domiciled neocloud."),
 ("IREN","IREN (ADR)",I,"Foreign (AU)",10,"",(3,4,7,4,4,3,2,7,2),0,"Unlikely; domicile","Australian; US sites don't fix the passport."),
 ("CIFR","Cipher Mining",I,"US",5,"",(3,3,8,6,4,3,1,7,2),0,"Unlikely","Converted miner; no strategic-input story."),
 ("APLD","Applied Digital",I,"US",10,"",(4,4,8,6,4,3,1,8,2),0,"Unlikely","Same; buildout without chokepoint."),
 ("WULF","TeraWulf",I,"US",5,"",(3,3,8,6,4,3,1,7,2),0,"Unlikely","Same."),
 ("EQIX","Equinix",I,"US",75,"",(2,4,2,5,4,3,1,6,1),0,"None","REIT; wrong shape."),
 ("DLR","Digital Realty",I,"US",55,"",(2,4,2,5,4,3,1,6,1),0,"None","Same."),
 ("VST","Vistra",I,"US",70,"",(2,5,2,6,5,5,1,7,2),0,"None; gets contracts/permits, not stakes",
  "Power gets PPAs and permitting relief; no conversion hook exists."),
 ("CEG","Constellation",I,"US",110,"",(3,6,2,6,5,6,1,7,2),0,"None; federal PPAs instead","Crane restart shows the state pays as customer, not owner."),
 ("NRG","NRG Energy",I,"US",35,"",(2,4,2,6,5,4,1,6,1),0,"None","Same."),
 ("TLN","Talen",I,"US",45,"",(2,5,2,6,4,4,1,7,1),0,"None","Same."),
 ("GEV","GE Vernova",I,"US",180,"",(3,8,2,6,6,6,2,7,2),0,"Turbine-capacity partnership at most","Gas-turbine chokepoint but healthy and unhooked."),
 ("OKLO","Oklo",I,"US",15,"",(8,6,7,9,9,9,3,8,5),0,
  "DOE pilot/fuel package with warrants; DoD microreactor anchor deals",
  "Administration darling: DOE reactor-pilot picks, INL fuel award, Altman-chaired history, deep MAGA-tech cap table. Pre-revenue capital needs meet maximal alignment - the Westinghouse logic says nuclear equity is thinkable."),
 ("SMR","NuScale",I,"US",5,"",(6,5,7,8,6,8,3,6,4),0,"DOE program equity if SMR orders firm up","Certified SMR design; weaker alignment halo than Oklo."),
 ("NNE","Nano Nuclear",I,"US",1.5,"",(4,3,8,7,5,6,2,4,2),0,"Speculative","Early-stage microreactor."),
 ("LEU","Centrus Energy",I,"US",6,"",(10,10,8,9,6,10,4,8,5),0,
  "Equity/warrants attached to the $900M+ DOE HALEU task-order buildout (Intel-conversion logic on live federal money)",
  "The single cleanest pattern-match left: only US-owned enrichment path, born of USEC privatization, $900M DOE task order (Jan 2026) inside a $3.4B program, Russia-dependence narrative, capital-hungry Piketon expansion. Every factor the framework rewards."),
 ("BWXT","BWX Technologies",I,"US",15,"",(9,9,4,8,7,9,3,6,3),0,
  "L3Harris-style unit-level equity (e.g., commercial HALEU/TRISO unit) rather than parent stake",
  "Sole-source naval reactors + TRISO; no distress, so the lane is Aerojet-style division equity, not rescue."),
 ("UEC","Uranium Energy",I,"US",5,"",(5,6,6,8,6,7,4,5,3),0,"Strategic-reserve offtake + warrants","US uranium supply narrative; stockpile buyer exists."),
 ("CCJ","Cameco (ADR)",I,"Foreign (CA)",40,"",(5,8,3,4,6,7,3,5,4),0,
  "Already exposed via Westinghouse profit-share/IPO-warrant structure (49% owner)",
  "The public-market proxy for the govt's Westinghouse economics; Canadian domicile caps direct-stake odds."),
 ("VRT","Vertiv",I,"US",50,"",(2,5,2,6,4,4,2,6,1),0,"None","Thermal/power gear; no hooks."),
 ("SMCI","Supermicro",I,"US",30,"",(3,4,4,6,5,3,3,7,1),0,"Unlikely","US assembly story only."),
 ("ANET","Arista",I,"US",120,"",(2,5,2,6,4,3,2,5,1),0,"None","Healthy, unhooked."),
 ("DELL","Dell",I,"US",90,"",(4,4,2,6,7,4,3,7,2),0,"None; wins as vendor","Federal AI-factory vendor, not target."),
 ("HPE","HPE",I,"US",30,"",(4,4,3,6,5,4,3,5,1),0,"None","Same."),
 ("PWR","Quanta Services",I,"US",55,"",(2,4,2,6,4,4,1,6,1),0,"None","Grid EPC; contracts not stakes."),
 ("MOD","Modine",I,"US",8,"",(2,4,3,6,4,3,1,6,1),0,"None","Cooling; no lane."),

 # ---- AI software, hyperscale & defense AI
 ("MSFT","Microsoft",A,"US",2830,"",(4,7,3,4,6,6,4,8,4),0,
  "Only via the multi-lab 'donation' scheme if it becomes policy",
  "OpenAI's patron but not named in the 5%-each reporting; size makes anything but donation impossible."),
 ("GOOGL","Alphabet",A,"US",4310,"",(6,8,5,5,6,7,4,8,8),0,
  "5% 'Public Wealth Fund' donation-for-relief structure (named in FT-reported proposal)",
  "Explicitly named in the OpenAI-floated arrangement. The currency isn't rescue capital - it's antitrust/copyright/preemption relief priced as equity. Watch the Aug 1 framework and any settlement talk."),
 ("META","Meta",A,"US",1900,"",(5,7,5,5,7,6,3,8,8),0,
  "Same donation-model lane; named in reporting",
  "Zuckerberg has courted the administration hard; named alongside Google/Anthropic in the 5% concept."),
 ("AMZN","Amazon",A,"US",2600,"",(4,6,3,4,6,5,3,8,3),0,"Donation lane only, not named yet","AWS+Anthropic angle; no direct signal."),
 ("AAPL","Apple",A,"US",4300,"",(4,4,5,4,8,5,8,9,2),0,"None; pays in US-investment pledges",
  "The $600B pledge model: Apple buys relief with capex promises (incl. MP offtake), not equity."),
 ("ORCL","Oracle",A,"US",700,"",(6,6,4,5,9,6,4,9,4),0,
  "Stargate/TikTok-adjacent structures; unlikely direct stake",
  "Deepest personal alignment (Ellison) and the TikTok JV shows how they transact - control structures, not stakes."),
 ("IBM","IBM",A,"US",340,"STAKED-LOI",(8,7,5,8,8,8,4,7,6),0,
  "Already in: $1B quantum LOI into new 'Anderon' unit with matching investment; further tranches plausible",
  "Biggest quantum-9 beneficiary. The unit-level structure (govt equity in a carved-out frontier unit) may become the template for healthy large caps."),
 ("PLTR","Palantir",A,"US",350,"",(9,7,2,6,10,8,3,5,4),0,
  "Unlikely equity; the relationship monetizes as contracts",
  "Maximal alignment, zero need - the government showers it with contracts instead. High presence, low event probability."),
 ("AI","C3.ai",A,"US",2,"",(6,4,7,7,4,5,2,3,2),0,"Distressed gov-AI consolidation target","Federal footprint, struggling; more M&A than stake story."),
 ("BBAI","BigBear.ai",A,"US",2,"",(6,4,8,7,5,6,2,3,3),0,"Small defense-AI equity package conceivable","Border/defense AI narrative fits; tiny and cash-hungry."),
 ("SOUN","SoundHound",A,"US",4,"",(3,3,6,7,4,3,2,2,1),0,"None","No strategic hook."),
 ("LDOS","Leidos",A,"US",25,"",(8,5,2,7,6,6,2,4,2),0,"None; healthy services prime","Contracts, not equity."),
 ("BAH","Booz Allen",A,"US",12,"",(8,4,3,7,5,5,2,3,2),0,"None","Same, plus VC arm optics."),
 ("SAIC","SAIC",A,"US",6,"",(8,4,3,7,5,5,2,3,2),0,"None","Same."),
 ("CACI","CACI",A,"US",12,"",(8,4,2,7,5,5,2,3,2),0,"None","Same."),
 ("PSN","Parsons",A,"US",9,"",(7,4,3,7,5,5,2,3,2),0,"None","Same."),
 ("KTOS","Kratos",A,"US",15,"",(8,6,6,8,7,8,3,6,4),0,
  "Unit-level equity in drone/engine JVs or DPA package as attritable-mass buildout accelerates",
  "Purest listed play on the drone/CCA budget surge; capital-intensive scaling gives the govt an entry point L3Harris just legitimized."),
 ("AVAV","AeroVironment",A,"US",15,"",(8,6,5,8,7,8,3,6,4),0,"Same lane as KTOS","Switchblade/Jump scaled by the $1.5T budget; slightly less need."),
 ("RCAT","Red Cat",A,"US",2,"",(7,5,8,8,6,7,3,4,3),0,"Small DPA equity package","Army SRR winner, cash-hungry microcap - TMQ risk/reward shape."),
 ("ONDS","Ondas",A,"US",3,"",(6,4,8,8,5,6,3,4,2),0,"Same","Drone/counter-drone smallcap."),
 ("LMT","Lockheed Martin",A,"US",110,"",(10,8,4,7,6,8,3,5,8),0,
  "Golden-share-style rights or unit-level equity; Lutnick named it explicitly ('97% of revenue from USG')",
  "The only company an official has named as a stake candidate on the record. F-35 dependence cuts both ways: total leverage, but no crisis to price against - expect structure, not size."),
 ("RTX","RTX",A,"US",200,"",(9,7,3,6,6,7,3,5,5),0,"Munitions-unit equity in a surge package","Rev dependence + munitions surge; healthy parent."),
 ("NOC","Northrop",A,"US",90,"",(9,7,3,6,6,7,3,5,5),0,"Same","B-21/nukes; same shape."),
 ("GD","General Dynamics",A,"US",90,"",(9,6,3,6,6,7,3,5,5),0,"Submarine-industrial-base equity package","AUKUS sub-base money already flows; equity twist conceivable."),
 ("HII","Huntington Ingalls",A,"US",12,"",(9,7,6,7,6,9,3,6,5),0,
  "Shipyard-modernization equity/warrant package (shipbuilding is a named budget priority)",
  "Sole-ish builder of carriers/amphibs with real capital needs and a $65.8B shipbuilding budget aimed at it - the defense name where 'need' actually exists."),
 ("LHX","L3Harris",A,"US",60,"STAKED-LOI",(9,6,5,8,7,8,3,5,9),0,
  "Already in: $1B Pentagon investment converting to equity at Aerojet unit IPO (H2 2026)",
  "First defense-prime equity structure; the unit-IPO conversion is the template to watch — and the IPO itself is a 2H26 catalyst."),

 # ---- Strategic materials & frontier tech
 ("MP","MP Materials",M,"US",15,"STAKED",(10,10,6,9,8,10,9,8,6),0,
  "Second tranche: magnet 10X expansion, heavy-RE separation, stockpile (Project Vault) offtakes",
  "The prototype deal. DoD is the largest shareholder with a price floor; every expansion phase invites more government paper."),
 ("USAR","USA Rare Earth",M,"US",4,"STAKED-LOI",(9,8,8,9,7,9,8,7,5),0,
  "LOI (Jan 2026): $1.3B loan + $277M for 8-16% - definitive docs are the next event",
  "Second RE platform blessed; definitive close and tranche timing are tradeable milestones."),
 ("LAC","Lithium Americas",M,"US",2,"STAKED",(9,7,7,9,6,8,6,6,4),0,
  "Additional support as Thacker Pass phases fund","DOE holds 5%+5% via penny warrants after loan rework."),
 ("TMQ","Trilogy Metals",M,"US",2,"STAKED",(8,7,8,9,6,8,7,5,4),0,
  "Warrant exercise (+7.5%) and Ambler road buildout","The +211%-in-a-day precedent; now a policy instrument."),
 ("UUUU","Energy Fuels",M,"US",5,"",(7,9,8,9,6,10,8,7,7),0,
  "MP-style package: equity/warrants + price floor + offtake around White Mesa REE separation",
  "Only conventional uranium mill + operating US RE separation. Sits at the exact intersection of the two doctrines (nuclear fuel + rare earths) with an official saying more minerals stakes are coming."),
 ("NB","NioCorp",M,"US",1,"",(7,8,9,8,5,8,8,5,6),0,
  "EXIM-loan-linked equity/warrants for Elk Creek (USAR template)",
  "Niobium/scandium/titanium with zero domestic production today; EXIM engagement is the pre-positioned hook."),
 ("PPTA","Perpetua Resources",M,"US",3,"",(9,9,9,9,6,9,9,7,7),0,
  "DPA-linked equity/warrants around Stibnite construction financing (EXIM $1.8B LOI already outstanding)",
  "The purest MP clone left: only US antimony path (China banned exports), already DPA-funded, EXIM LOI in hand, gold by-product de-risks. If the framework works, this is what it was built to find."),
 ("TMC","TMC the metals co.",M,"US",3,"",(6,7,9,6,7,8,8,6,7),0,
  "Equity/royalty attached to NOAA commercial recovery permit + stockpile offtake (permission-pricing lane)",
  "NOAA permit in full-compliance review toward early-2027 award; the seabed EO created the lane and TMQ showed how permits get priced."),
 ("CRML","Critical Metals Corp",M,"US-listed (Greenland assets)",1,"",(7,8,9,5,6,8,8,4,8),0,
  "Reported prospective US equity stake + EXIM $120M LOI for Tanbreez",
  "Stake talks already reported; Greenland politics and the Saudi processing JV are the complications."),
 ("METC","Ramaco Resources",M,"US",1.5,"",(5,6,8,8,6,7,7,5,5),0,
  "Brook Mine REE support package","Coal-to-REE story courting the administration; earlier-stage than the leaders."),
 ("UAMY","US Antimony",M,"US",0.5,"",(5,7,7,7,4,7,8,4,3),0,
  "Small DPA offtake/equity","Only US antimony smelter; microcap lottery-ticket shape."),
 ("AA","Alcoa",M,"US",10,"",(4,6,4,7,5,6,5,5,3),0,
  "Gallium package (Atlantic Alumina precedent)","Gallium byproduct potential echoes the Pentagon's alumina deal."),
 ("CENX","Century Aluminum",M,"US",3,"",(5,7,5,7,5,7,6,5,4),0,
  "Smelter-restart support with equity kicker","Primary aluminum + gallium adjacency; Section-232 favorite."),
 ("ASPI","ASP Isotopes",M,"US-listed (SA ops)",1.5,"",(4,6,7,4,4,7,4,4,3),0,
  "HALEU-adjacent enrichment support; domicile haircut","Isotope enrichment story, South African operations."),
 ("IONQ","IonQ",M,"US",12,"",(6,6,7,7,4,8,4,5,5),-5,
  "Rehabilitation tranche after being passed over in the quantum-9",
  "Excluded from the May package amid the Wolfpack short report and the Feinberg/Cerberus conflict optics. A cleanup + re-inclusion is possible but the cloud is real."),
 ("RGTI","Rigetti",M,"US",8,"STAKED-LOI",(7,6,7,8,6,8,4,5,5),0,
  "LOI signed ($100M/equity); definitive close + follow-on tranches","Inside the tent; superconducting track."),
 ("QBTS","D-Wave",M,"US",10,"STAKED-LOI",(7,6,7,8,6,8,4,5,5),0,
  "LOI signed ($100M/equity); definitive close + follow-ons","Inside the tent; annealing niche."),
 ("QUBT","Quantum Computing Inc",M,"US",3,"",(3,4,8,7,3,6,3,3,3),-2,
  "Unlikely; passed over","Sympathy-mover without a federal anchor."),
 ("INFQ","Infleqtion",M,"US",3,"STAKED-LOI",(6,5,7,7,5,7,4,4,4),0,
  "LOI signed ($100M/equity)","Quantum sensing/atomics; newly public."),
 ("ARQQ","Arqit (ADR)",M,"Foreign (UK)",0.5,"",(2,4,7,3,3,5,3,2,2),0,"Unlikely; UK","Post-quantum crypto ADR; sympathy trade only."),
]

def composite(scores, penalty):
    total = sum(s * W[k] for s, k in zip(scores, ORDER)) / 10.0
    return round(total + penalty, 1)

ROWS = []
for t, n, sub, dom, cap, status, sc, pen, mech_note, why in UNIVERSE:
    ROWS.append({
        "ticker": t, "name": n, "subsector": sub, "domicile": dom,
        "cap": cap, "status": status, "scores": sc, "penalty": pen,
        "composite": composite(sc, pen), "mech_note": mech_note, "why": why,
    })
ROWS.sort(key=lambda r: -r["composite"])

NEXT = [r for r in ROWS if r["status"] in ("", "EXEMPTED")]

# --------------------------------------------------- deal precedent table ---
DEALS = [
 ("2025-07-10","MP Materials","MP","DoD","$400M pref + warrant = ~15%; $110/kg NdPr floor 10yr; 100% magnet offtake; $150M loan","Chokepoint rescue-scale-up","+50% D1; +85% July"),
 ("2025-06","US Steel","X","White House/CFIUS","Golden share (veto rights) as Nippon merger condition","Permission priced as control","n/a"),
 ("2025-08-11","NVIDIA / AMD","NVDA/AMD","Commerce/WH","15% of China H20/MI308 revenue for export licenses (2026: reported 25% on H200 deal)","Permission priced as revenue share","muted; licenses = upside"),
 ("2025-08-22","Intel","INTC","Commerce/DoD","433.3M sh @ $20.47 = 9.9% (~$8.9B) converting $5.7B CHIPS + $3.2B Secure Enclave; 5% warrant @ $20 (foundry <51% trigger)","Grant conversion into distressed chokepoint","+~7% D1; ~5x by mid-2026"),
 ("2025-10-06","Trilogy Metals","TMQ","White House/DoD","$35.6M for 10% + 7.5% warrants; Ambler road permits unlocked","Permit priced as equity","+211% D1 (intraday ~260%)"),
 ("2025-10-07","Lithium Americas","LAC","DOE","5% penny warrants + 5% JV stake for $184M debt-service deferral on $2.26B ATVM loan","Loan renegotiation priced as equity","+~90-100% on Sep 24 leak"),
 ("2025-10-28","Westinghouse (private; CCJ/BN own)","-","Commerce","$80B AP1000 program; 20% profit share above $17.5B; IPO-forcing right + 20% equity warrants by Jan 2029","New-build program priced as profit share","CCJ/BN rallied"),
 ("2025-12","L3Harris (Aerojet unit)","LHX","DoD","Proposed $1B into rocket-motor business; converts to common equity at unit IPO (H2 2026)","Unit-level equity in healthy prime","modest pop"),
 ("2026-01-26","USA Rare Earth","USAR","Commerce","LOI: $1.3B loan + $277M funding for shares/warrants = 8-16%","USAR = second MP","sharp rally"),
 ("2026-02","Atlantic Alumina","-","DoD","$150M equity for first US gallium production","Input-security equity","n/a"),
 ("2026-05-21","Quantum-9 (IBM $1B, GFS $375M, QBTS/RGTI/INFQ $100M ea, Diraq $38M; + Atom, PsiQuantum, Quantinuum)","IBM,GFS,QBTS,RGTI,INFQ","Commerce/NIST","$2.013B CHIPS LOIs; minority non-controlling equity in each; IonQ excluded","Sector-wide frontier-tech equity sweep","QBTS/RGTI jumped; sympathy: ARQQ +25%, IONQ +12%, QUBT +19%"),
 ("2026-06/07","OpenAI (private) + 'leading AI developers'","-","White House","Talks: OpenAI proposes 5% (~$42.6B of $852B) donated to seed a Public Wealth Fund; concept: 5% of each leading lab incl. Anthropic, Google, Meta","Donation-for-relief model (proposed)","pending"),
]

# ------------------------------------------------------------------ excel ---
def build_xlsx(path):
    wb = Workbook()
    thin = Border(*[Side(style="thin", color="D9D9D9")]*4)
    hdr_fill = PatternFill("solid", fgColor="1F3864")
    hdr_font = Font(color="FFFFFF", bold=True)
    staked_fill = PatternFill("solid", fgColor="FFF2CC")

    def style_header(ws, ncols, row=1):
        for c in range(1, ncols+1):
            cell = ws.cell(row=row, column=c)
            cell.fill = hdr_fill; cell.font = hdr_font
            cell.alignment = Alignment(wrap_text=True, vertical="center")

    def sheet_scorecard(ws, rows, title_note):
        cols = ["Rank","Ticker","Company","Subsector","Domicile","Mkt cap ≈$B","Status",
                *[f"{FACTORS[k][1]} (w={W[k]})" for k in ORDER],
                "Penalty","Composite /100","Most-likely mechanism","Why (one-liner)"]
        ws.append(cols); style_header(ws, len(cols))
        for i, r in enumerate(rows, 1):
            ws.append([i, r["ticker"], r["name"], r["subsector"], r["domicile"], r["cap"],
                       r["status"] or "-", *r["scores"], r["penalty"], r["composite"],
                       r["mech_note"], r["why"]])
            if r["status"].startswith("STAKED") or r["status"]=="REV-SHARE":
                for c in range(1, len(cols)+1):
                    ws.cell(row=i+1, column=c).fill = staked_fill
        comp_col = get_column_letter(8 + len(ORDER) + 1 + 1)  # after 7 id cols + factors + penalty… compute below
        # compute composite column index precisely: 7 id cols, 9 factors, 1 penalty -> composite = 18
        comp_idx = 7 + len(ORDER) + 1 + 1
        letter = get_column_letter(comp_idx)
        ws.conditional_formatting.add(
            f"{letter}2:{letter}{len(rows)+1}",
            ColorScaleRule(start_type="num", start_value=25, start_color="F8696B",
                           mid_type="num", mid_value=60, mid_color="FFEB84",
                           end_type="num", end_value=90, end_color="63BE7B"))
        widths = [6,8,22,26,14,11,12]+[13]*len(ORDER)+[9,11,46,60]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.border = thin
                if cell.column >= len(cols)-1:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = ws.dimensions
        ws.sheet_properties.tabColor = "1F3864"

    ws = wb.active; ws.title = "Next-Name Ranking"
    sheet_scorecard(ws, NEXT, "ex-already-staked")
    ws2 = wb.create_sheet("Full Scorecard (all)")
    sheet_scorecard(ws2, ROWS, "all")

    ws3 = wb.create_sheet("By Subsector")
    cols = ["Subsector","Rank in sub","Ticker","Company","Composite","Status","Most-likely mechanism"]
    ws3.append(cols); style_header(ws3, len(cols))
    for sub in [S, I, A, M]:
        subrows = [r for r in ROWS if r["subsector"] == sub]
        for j, r in enumerate(subrows, 1):
            ws3.append([sub, j, r["ticker"], r["name"], r["composite"], r["status"] or "-", r["mech_note"]])
    for i, w in enumerate([34,10,8,24,11,12,60], 1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    ws4 = wb.create_sheet("Factor Definitions")
    ws4.append(["Factor","Weight","Name","Scoring rubric"]); style_header(ws4, 4)
    for k in ORDER:
        ws4.append([k, W[k], FACTORS[k][1], FACTORS[k][2]])
    ws4.append(["penalty","0 to -10","Anti-signals","Explicit exemption statements (MU/TSM/TXN), short-seller clouds & prior exclusion (IONQ), adversarial CEO posture. Subtracted from weighted composite."])
    for i, w in enumerate([10,8,28,110], 1):
        ws4.column_dimensions[get_column_letter(i)].width = w
    for row in ws4.iter_rows(min_row=2):
        row[3].alignment = Alignment(wrap_text=True, vertical="top")

    ws5 = wb.create_sheet("Deal Precedents")
    ws5.append(["Date","Company","Ticker(s)","Agency","Terms","Pattern","Stock reaction"]); style_header(ws5, 7)
    for d in DEALS: ws5.append(list(d))
    for i, w in enumerate([11,34,14,14,70,32,26], 1):
        ws5.column_dimensions[get_column_letter(i)].width = w
    for row in ws5.iter_rows(min_row=2):
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws6 = wb.create_sheet("Notes & Caveats")
    notes = [
        "Data vintage 2026-07-06. Market caps are approximate, web-sourced; verify before sizing (several names moved multiples in the past year, e.g., INTC ~5x since the Aug 2025 stake).",
        "Composite = sum(factor score x weight)/10 + penalty; 0-100 scale. Scores are analyst judgments calibrated to the deal-precedent back-cast (see REPORT.md section 4).",
        "Status: STAKED = closed deal; STAKED-LOI = signed letter of intent; REV-SHARE = export-license revenue share; EXEMPTED = Commerce publicly ruled out equity.",
        "The 'Next-Name Ranking' tab excludes names already inside a stake/LOI/rev-share structure; they carry separate second-tranche catalysts (Full Scorecard tab).",
        "This is a likelihood screen, not investment advice; announcement timing is not modeled - the trading playbook in REPORT.md addresses expression.",
    ]
    ws6.append(["Notes"]); style_header(ws6, 1)
    for n in notes: ws6.append([n])
    ws6.column_dimensions["A"].width = 130
    for row in ws6.iter_rows(min_row=2):
        row[0].alignment = Alignment(wrap_text=True, vertical="top")

    wb.save(path)

# -------------------------------------------------------------- markdown ----
def md_tables():
    out = []
    out.append("### Next-name ranking (top 25, excludes already-staked)\n")
    out.append("| # | Ticker | Company | Subsector | ≈Cap $B | Composite | Most-likely mechanism |")
    out.append("|---|--------|---------|-----------|---------|-----------|----------------------|")
    for i, r in enumerate(NEXT[:25], 1):
        out.append(f"| {i} | **{r['ticker']}** | {r['name']} | {r['subsector'].split(' ')[0]} {r['subsector'].split(' ')[1] if len(r['subsector'].split(' '))>1 else ''} | {r['cap']} | **{r['composite']}** | {r['mech_note']} |")
    out.append("")
    for sub in [S, I, A, M]:
        out.append(f"\n### {sub}\n")
        out.append("| Rank | Ticker | Company | ≈Cap $B | Status | Composite | Mechanism if it happens |")
        out.append("|------|--------|---------|---------|--------|-----------|------------------------|")
        for j, r in enumerate([x for x in ROWS if x["subsector"]==sub], 1):
            out.append(f"| {j} | {r['ticker']} | {r['name']} | {r['cap']} | {r['status'] or '—'} | {r['composite']} | {r['mech_note']} |")
    return "\n".join(out)

if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    build_xlsx(os.path.join(here, "gov_ai_stake_screen.xlsx"))
    with open(os.path.join(here, "scorecard_tables.md"), "w") as f:
        f.write(md_tables())
    print(f"Universe: {len(ROWS)} names; next-name pool: {len(NEXT)}")
    print("Top 15 next names:")
    for i, r in enumerate(NEXT[:15], 1):
        print(f"{i:2d}. {r['ticker']:6s} {r['composite']:5.1f}  {r['name']}")
