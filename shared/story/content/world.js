// OVERDUE story content: the world registry (districts, factions, places, standing, endings).
// Everything else in shared/story/content points at ids defined here. Plain data, no imports, no Node or DOM APIs.
//
// SCHEMA
//   DISTRICTS[id] = { name, ruler (a FACTIONS id at the start of the game), takeover (the group that can take it, or
//                     null), clock (how its district clock runs), opens (act it opens in), gross (0-10 dial, DESIGN §7.2),
//                     blurb }
//   FACTIONS[id]  = { name, kind: 'company' | 'group', colour, leader (a cast id), blurb }
//   LOCATIONS[id] = { district, name, desc }    id is '<district>:<place>', stable, used by quest markers and scenes
//   STANDING      = the standing meters a save tracks ({ id: { name, min, max } })
//   ENDINGS[id]   = { name, canon, blurb }
//   SPEAKERS      = speaker ids that are allowed in dialogue and scenes without being in the cast (crowds, signs, radio)
//
// IDS: lowercase, snake_case, never renamed once shipped (saves store them). Add, don't rename.
//
// CONDITION and ACTION strings (used by `if` and `do` everywhere in the content; the test checks every one):
//   conditions (`if`, a string; space-separated terms are ANDed; a leading ! negates one term):
//     flag:<flag>            the flag is set                       done:<mission>      the mission is finished
//     active:<mission>       the mission is in progress            has:<item>          the item is in the bag
//     standing.<s><op><n>    standing compare (op: >= <= > < =)    drift<op><n>        Drift compare
//     turf.<district>=<faction>  who runs a district               fate.<cast>=<state> a character's state
//     cats<op><n>            board cats petted                     frags.<set><op><n>  memory fragments found
//     act<op><n>             current act                           implant:<implant>   the implant is installed
//     pages<op><n>           Option C pages collected (0-6)        plan=<lumps|gordo|auntie>  whose plan the raid follows
//     clock.<district>=<hh:mm-hh:mm>  the district clock is inside that window
//   actions (`do`, an array of strings, run in order):
//     flag:<flag>  unflag:<flag>  start:<mission>  give:<item>  take:<item>  coupons:<+n|-n>  standing.<s>:<+n|-n>
//     turf:<district>=<faction>  scene:<scene>  boss:<boss>  drift:<+n|-n>  fate:<cast>=<state>  implant:<implant>
//     collect:<collectible>  loot:<loot table>  unlock:<location>  fees:<+n|-n> (Late Fees stars)  call:<cast> (a pager call)
//   fate states: alive, dead, gut (taken to the Gut), freed, gone (left the city), clocked_out, terminated, signed

export const DISTRICTS = {
  bottom: { name: 'THE BOTTOM', ruler: 'bottom', takeover: null, clock: 'about right, give or take a lunch', opens: 1, gross: 3,
    blurb: 'An Off-Spec survivor town on the crust of the corpse-city. Dig anywhere and you hit bone.' },
  gut: { name: 'THE GUT', ruler: 'gristle', takeover: 'bottom', clock: "doesn't care. it's always dinner", opens: 1, gross: 10,
    blurb: "The valley where the war's dead were piled. Regrowth got into them. It digests. It loves you." },
  pinstripe: { name: 'PINSTRIPE', ruler: 'family', takeover: 'punchlines', clock: 'twenty minutes slow, fashionably', opens: 2, gross: 6,
    blurb: 'Fazzoletti Family Insurance insured every side of the war and came through untouched.' },
  checkout: { name: 'THE CHECKOUT', ruler: 'bigvalue', takeover: 'mallrats', clock: 'always 09:00 somewhere: the doors open every hour', opens: 2, gross: 3,
    blurb: "Big Value's flagship mall. The doors only opened for members. The sale never stopped." },
  numberworks: { name: 'NUMBER WORKS', ruler: 'remainder', takeover: 'remainders', clock: 'runs in decimals', opens: 2, gross: 3,
    blurb: 'Remainder Industries calculated the war. Now it prints the prices.' },
  chromegristle: { name: 'CHROME GRISTLE', ruler: 'meatmechanics', takeover: null, clock: 'always night, always 23:59', opens: 3, gross: 6,
    blurb: 'The old Neon Market. Organs from the Gut, installed, swapped, pawned and stolen.' },
  evergreen: { name: 'EVERGREEN ACRES', ruler: 'hoa', takeover: null, clock: 'a perfect sitcom afternoon, forever', opens: 3, gross: 1,
    blurb: 'A fallout-shelter suburb that came back up and refuses to admit anything happened.' },
  lates: { name: 'THE LATES', ruler: 'loopers', takeover: null, clock: 'Tuesday. 09:00 to 17:30, again', opens: 3, gross: 4,
    blurb: "Where ☺ CORP's Schedule Bomb went off. It has been the same Tuesday for sixty-one years." },
  margins: { name: 'THE MARGINS', ruler: 'vacancy', takeover: 'marginwalkers', clock: 'dusk, getting later', opens: 4, gross: 4,
    blurb: 'The edge of the world, where the void bombs deleted the land. Plots still for sale.' },
  corphill: { name: 'CORP HILL', ruler: 'corp', takeover: null, clock: 'exactly on time', opens: 4, gross: 1,
    blurb: 'The top of the hill and the only place that still looks like before. Business as usual.' },
  commute: { name: 'THE COMMUTE', ruler: 'unpaid', takeover: null, clock: 'rush hour, permanently', opens: 1, gross: 5,
    blurb: 'Dead highways jammed with the evening rush of the Final Quarter. Paper storms. Raiders.' },
  sims: { name: 'THE TRAINING SIMS', ruler: 'corp', takeover: null, clock: 'the last workday', opens: 1, gross: 0,
    blurb: "Inside the Machine. The world before the war, played by people who don't know they're dead." },
};
export const DISTRICT_IDS = Object.keys(DISTRICTS);

export const FACTIONS = {
  corp: { name: '☺ CORP', kind: 'company', colour: '#4fd8ff', leader: 'hask', blurb: 'Smiling, punctual, plastic, in total denial. Business as usual.' },
  gristle: { name: 'GRISTLE & SONS BIOLOGICS', kind: 'company', colour: '#ff6f91', leader: 'bishop', blurb: 'Organic growth. The staff stayed at their desks while the building grew around them.' },
  bigvalue: { name: 'BIG VALUE RETAIL', kind: 'company', colour: '#ffe14d', leader: 'gail', blurb: 'Every ration in the city. Everyone a customer.' },
  family: { name: 'FAZZOLETTI FAMILY INSURANCE', kind: 'company', colour: '#c0202a', leader: 'nonna', blurb: "A family business since 1850. You're covered. You're always covered." },
  remainder: { name: 'REMAINDER INDUSTRIES', kind: 'company', colour: '#ff9a1a', leader: 'mr_sevens', blurb: 'Whoever prints the prices runs the market.' },
  vacancy: { name: 'VACANCY HOLDINGS', kind: 'company', colour: '#202028', leader: 'penny_plot', blurb: 'Premium negative space. Location, location, nothing.' },
  bottom: { name: 'THE BOTTOM', kind: 'group', colour: '#ffb3c7', leader: 'auntie', blurb: 'Off-Spec families three generations deep. They want up the hill.' },
  unpaid: { name: 'THE UNPAID', kind: 'group', colour: '#8a8a8a', leader: 'eotm', blurb: "Intern raiders in office-chair armour. They're doing a startup." },
  fundept: { name: 'THE FUN DEPARTMENT', kind: 'group', colour: '#ff00dc', leader: 'morale_officer', blurb: 'Feral ex-Marketing mascots. Fun is mandatory.' },
  punchlines: { name: 'THE PUNCHLINES', kind: 'group', colour: '#b07dff', leader: 'pip', blurb: "The Don's jesters and every clown he ever laughed at." },
  mallrats: { name: 'THE MALL RATS', kind: 'group', colour: '#7dff4f', leader: 'wristband', blurb: 'Families who have lived in the air vents since the Stampede.' },
  remainders: { name: 'THE REMAINDERS', kind: 'group', colour: '#ffd27a', leader: 'nell', blurb: 'A union of people stamped with the numbers nobody wanted.' },
  meatmechanics: { name: 'THE MEAT MECHANICS', kind: 'group', colour: '#ff3030', leader: 'upsell', blurb: 'Scavenger surgeons. Their logo is a kidney. They want to be a company.' },
  hoa: { name: 'THE HOA', kind: 'group', colour: '#7dc85a', leader: 'linda', blurb: 'An armed homeowners association. Property values above all.' },
  loopers: { name: 'THE LOOPERS', kind: 'group', colour: '#e8d27a', leader: 'pauline', blurb: "Stuck in the same Tuesday for sixty-one years. They'd like Wednesday." },
  marginwalkers: { name: 'THE MARGIN WALKERS', kind: 'group', colour: '#4a7a4a', leader: 'old_pat', blurb: 'Lonely people who stake the ground with garden gnomes so the void stops.' },
};
export const FACTION_IDS = Object.keys(FACTIONS);

export const STANDING = { corp: { name: 'CORP STANDING', min: -100, max: 100 }, bottom: { name: 'BOTTOM STANDING', min: -100, max: 100 } };

export const ENDINGS = {
  on_time: { name: 'ON TIME', canon: true, blurb: "You sign. The Restoration runs. Everyone is fed, and nobody is free, including you." },
  late: { name: 'LATE', canon: true, blurb: 'You smash the Master Clock. Nobody owns time. Nobody keeps the lights on either.' },
  off_books: { name: 'OFF THE BOOKS', canon: true, blurb: 'You publish Option C. The debts die. The people who ended the world have to bargain.' },
  nap_time: { name: 'NAP TIME', canon: false, blurb: "The founder walks across the keyboard. This didn't happen." },
};

// speakers that aren't characters
export const SPEAKERS = ['narrator', 'pa', 'radio', 'crowd', 'sign', 'pager', 'machine', 'hud', 'kid', 'choir', 'officer', 'raider', 'shopper', 'looper', 'agent', 'goon', 'intern', 'nurse', 'voice'];

// LOCATIONS: '<district>:<place>'
export const LOCATIONS = {
  // the bottom
  'bottom:lostfound': { district: 'bottom', name: 'The Lost & Found', desc: 'A ruined returns depot. The hub safehouse. Home of the Machine.' },
  'bottom:machine': { district: 'bottom', name: 'The Machine', desc: 'The original ☺ vending machine. Still humming. Nothing can kill it.' },
  'bottom:long_stairs': { district: 'bottom', name: 'The Long Stairs', desc: '1,000 steps up to the Gut border. The settlers are buried under the steps.' },
  'bottom:gym': { district: 'bottom', name: "Lumps' Gym", desc: 'All the weights are fridges.' },
  'bottom:down_escalator': { district: 'bottom', name: 'The Down Escalator', desc: 'Broken. It only goes down.' },
  'bottom:sunset_spot': { district: 'bottom', name: 'The Sunset Wall', desc: 'A wall on the top terrace where Lumps watches the sunset. He cries. Everyone lets him.' },
  'bottom:soup_kitchen': { district: 'bottom', name: "Sharon's Soup Kitchen", desc: 'Big pots. The Bottom trades soup for medicine.' },
  'bottom:landlord_pile': { district: 'bottom', name: 'The Deposit Pile', desc: "The biggest pile of rubble in the Bottom. Mr. Deposit says he owns it." },
  'bottom:rooftops': { district: 'bottom', name: 'The Wok Roofs', desc: 'Stacked roofs with satellite dishes made of woks.' },
  'bottom:gordo_den': { district: 'bottom', name: "Gordo's Den", desc: 'A shipping container full of maps, string and stolen ☺ CORP binders.' },
  'bottom:dale_shed': { district: 'bottom', name: "Dale's Shed", desc: 'Behind the Machine. Forty years of batteries, stacked like bricks.' },
  'bottom:school': { district: 'bottom', name: 'The Crayon School', desc: 'Where Auntie taught the Bottom to read. The walls are the textbook.' },
  // the gut
  'gut:border': { district: 'gut', name: 'The Gut Border', desc: 'Where the pastel houses start to grow skin. The first nemesis arena.' },
  'gut:stairs_top': { district: 'gut', name: 'Top of the Long Stairs', desc: 'Where the stairs go soft.' },
  'gut:big_stomach': { district: 'gut', name: 'The Big Stomach', desc: "The district's heart. A crater of churning acid lake." },
  'gut:peristalsis': { district: 'gut', name: 'Peristalsis Avenue', desc: 'The moving street. Slide in on the beat.' },
  'gut:choir_lung': { district: 'gut', name: 'The Choir Lung', desc: 'A cathedral that breathes.' },
  'gut:tooth_market': { district: 'gut', name: 'Tooth Market', desc: 'Everything costs teeth.' },
  'gut:campus': { district: 'gut', name: 'Gristle & Sons Campus', desc: 'The old Biologics HQ. Staff still at their desks, under the skin.' },
  'gut:digester_wall': { district: 'gut', name: 'The Digester Wall', desc: 'Where the Bottom\'s missing are, half grown in, still talking.' },
  'gut:feed_dock': { district: 'gut', name: 'The Feed Dock', desc: 'Where the Gristle & Sons trucks unload. Quiet. Always quiet.' },
  'gut:belly_button': { district: 'gut', name: 'The Belly Button', desc: "A door at the bottom of the Big Stomach. Don't press it." },
  'gut:clinic_bev': { district: 'gut', name: "Bev's Clinic", desc: "A back room on the Gut border. A dentist's chair. A bucket." },
  // pinstripe
  'pinstripe:villa': { district: 'pinstripe', name: 'Villa Fazzoletto', desc: 'A cathedral of marble and meatballs. The strings go up into the dark.' },
  'pinstripe:rafters': { district: 'pinstripe', name: 'The Rafters', desc: 'Above the Villa ceiling. Someone works the strings from here.' },
  'pinstripe:restaurant': { district: 'pinstripe', name: "Mamma Polizza's", desc: 'A checkerboard restaurant where the Family takes meetings.' },
  'pinstripe:sauce_works': { district: 'pinstripe', name: 'The Sauce Works', desc: 'The front business. A sauce factory with a red river.' },
  'pinstripe:respect_bridge': { district: 'pinstripe', name: 'Respect Bridge', desc: 'Pay respect to cross. Coupons accepted.' },
  'pinstripe:bocce_pit': { district: 'pinstripe', name: 'The Bocce Pit', desc: 'Where disputes are settled. The balls are heavy.' },
  'pinstripe:claims': { district: 'pinstripe', name: 'The Claims Office', desc: 'Every claim is denied.' },
  'pinstripe:clown_cellar': { district: 'pinstripe', name: 'The Green Room', desc: 'Under the Villa. Where the Punchlines rehearse.' },
  // the checkout
  'checkout:doors': { district: 'checkout', name: 'The Big Doors', desc: 'The doors. They open at 09:00. They have opened at 09:00 every day since the Stampede.' },
  'checkout:queue': { district: 'checkout', name: 'The Infinite Queue', desc: 'It winds round the district fourteen times.' },
  'checkout:food_court': { district: 'checkout', name: 'Food Court Colosseum', desc: 'A food court the size of a plaza. Fights at lunch.' },
  'checkout:escalator': { district: 'checkout', name: 'The Big Escalator', desc: '2 km up to Corp Hill. Employees only.' },
  'checkout:returns': { district: 'checkout', name: 'Returns Desk Zero', desc: 'The first returns desk. Nothing has ever been returned.' },
  'checkout:vents': { district: 'checkout', name: 'The Vents', desc: 'Where the Mall Rats live. Rope bridges, hammocks, a school.' },
  'checkout:pa_booth': { district: 'checkout', name: 'The PA Booth', desc: 'Where Gail has made the announcements for sixty-one years.' },
  'checkout:cart_corral': { district: 'checkout', name: 'The Cart Corral', desc: 'A car park full of carts. Something lives in it.' },
  // number works
  'numberworks:yard': { district: 'numberworks', name: 'The Number Yard', desc: 'Conveyor belts carrying giant numbers.' },
  'numberworks:smokestacks': { district: 'numberworks', name: 'The Smokestacks', desc: 'They puff digits.' },
  'numberworks:pit': { district: 'numberworks', name: 'The Remainder Pit', desc: 'Where leftover numbers go.' },
  'numberworks:calculator': { district: 'numberworks', name: 'The Big Calculator', desc: 'A building. The display is the top floor.' },
  'numberworks:prime_lane': { district: 'numberworks', name: 'Prime Lane', desc: 'Only prime-numbered houses. The rest were rounded off.' },
  'numberworks:press': { district: 'numberworks', name: 'The Price Press', desc: 'Where the city\'s prices are printed every morning.' },
  'numberworks:union_hall': { district: 'numberworks', name: 'Union Hall 13', desc: 'The Remainders\' hall. Thirteen chairs. Somebody always stands.' },
  'numberworks:archive': { district: 'numberworks', name: 'The Forecast Archive', desc: 'Every forecast Remainder ever made, on paper, on spools.' },
  // chrome gristle
  'chromegristle:pawn': { district: 'chromegristle', name: 'Organ Pawn', desc: 'Sell your organs. Buy them back later, at a markup.' },
  'chromegristle:upsell_clinic': { district: 'chromegristle', name: "Doctor Upsell's Clinic", desc: 'Twelve chairs. One doctor. Twelve arms.' },
  'chromegristle:arcade': { district: 'chromegristle', name: 'Arcade Row', desc: 'Cabinets that run the old JANKFIRE.' },
  'chromegristle:noodle_shrine': { district: 'chromegristle', name: 'The Noodle Shrine', desc: 'Noodles, offered to whoever is listening.' },
  'chromegristle:jar_alley': { district: 'chromegristle', name: 'Jar Alley', desc: 'Shelves of jars. Some of them blink.' },
  // evergreen acres
  'evergreen:culdesac': { district: 'evergreen', name: 'The Cul-de-sac', desc: 'Perfect houses in a perfect circle.' },
  'evergreen:clubhouse': { district: 'evergreen', name: 'The HOA Clubhouse', desc: 'Bylaws on every wall.' },
  'evergreen:pumpkin': { district: 'evergreen', name: 'The Prize Pumpkin', desc: 'It has won every year. It is the only entry.' },
  'evergreen:pool': { district: 'evergreen', name: 'The Community Pool', desc: "It's deep. It's very deep." },
  'evergreen:shelter': { district: 'evergreen', name: 'The Shelter', desc: 'Under the cul-de-sac. Where Evergreen waited out the Long Dark.' },
  'evergreen:charging_garage': { district: 'evergreen', name: 'Garage 03', desc: 'Every house has one. Something charges in it at 03:00.' },
  // the lates
  'lates:waiting_room': { district: 'lates', name: 'The Waiting Room', desc: 'Infinite, with chairs.' },
  'lates:tuesday_tower': { district: 'lates', name: 'Tuesday Tower', desc: 'A clock tower with no hands.' },
  'lates:stairwell': { district: 'lates', name: 'The Backrooms Stairwell', desc: 'Down to the basement. The basement is the Backrooms.' },
  'lates:remainder_office': { district: 'lates', name: 'Remainder Downtown Office', desc: 'Where Neville Brisk left at 09:00 with the revised numbers.' },
  'lates:canteen': { district: 'lates', name: 'The Canteen', desc: 'Tuesday lunch. It is always lasagne.' },
  'lates:missing_door': { district: 'lates', name: 'The Door in the Sky', desc: 'Only there at 03:00.' },
  'lates:warehouse': { district: 'lates', name: 'The Restoration Warehouse', desc: 'Mannequin bodies in rows to the horizon.' },
  // the margins
  'margins:bus_stop': { district: 'margins', name: 'The Last Bus Stop', desc: 'The bus is late. The road ends in nothing.' },
  'margins:hr_cabin': { district: 'margins', name: 'HR Cabin', desc: 'A cabin in the pines. Filing cabinets to the ceiling.' },
  'margins:edge': { district: 'margins', name: 'The Edge', desc: 'A cliff into the void, with a lifeguard tower.' },
  'margins:show_home': { district: 'margins', name: 'The Show Home', desc: "Vacancy Holdings' sales office. Every plot sold is a pin on the void." },
  'margins:gnome_field': { district: 'margins', name: 'The Gnome Field', desc: 'Where the Margin Walkers hold the line.' },
  'margins:forest': { district: 'margins', name: 'The Scary Forest', desc: 'Dark pines. The Tall Guy walks here.' },
  // corp hill
  'corphill:bleach_line': { district: 'corphill', name: 'The Bleach Line', desc: 'Where the rubble stops and the white starts.' },
  'corphill:dividend_road': { district: 'corphill', name: 'Dividend Road', desc: 'The road up to the Spire. Every clock faces it.' },
  'corphill:fountain': { district: 'corphill', name: 'The Smiling Fountain', desc: 'It smiles. It has always smiled.' },
  'corphill:museum': { district: 'corphill', name: 'The Punctuality Museum', desc: "Overtime's rehire arena. Exhibits about being on time." },
  'corphill:cathedral': { district: 'corphill', name: 'The Cathedral of Shareholder Value', desc: 'Pews facing a share price.' },
  'corphill:spire_lobby': { district: 'corphill', name: 'The ☺ Spire Lobby', desc: 'The same lobby as 17:29.' },
  'corphill:spire_60': { district: 'corphill', name: 'Spire, 60th Floor', desc: 'Internal Audit. Agnes Pell\'s old floor.' },
  'corphill:spire_top': { district: 'corphill', name: 'The Top Floor', desc: "Marion Hask's office." },
  'corphill:master_clock': { district: 'corphill', name: 'The Master Clock', desc: 'The top of the Spire. Gearwork the size of a cathedral.' },
  'corphill:clock_room': { district: 'corphill', name: 'The Clock Room', desc: 'Behind the Master Clock. A second, smaller Machine. Something is asleep on it.' },
  // the commute
  'commute:spiral_freeway': { district: 'commute', name: 'The Spiral Freeway', desc: 'A ramp that circles the hill four times.' },
  'commute:ring_road': { district: 'commute', name: 'The Ring Road', desc: 'Jammed with the evening rush of the Final Quarter.' },
  'commute:unpaid_camp': { district: 'commute', name: 'Camp Onboarding', desc: "The Unpaid's biggest camp. A bus depot made of desks." },
  'commute:carnival': { district: 'commute', name: 'The Fun Fair', desc: "The Fun Department's carnival. Only at night." },
  'commute:gary_crater': { district: 'commute', name: "Gary's Site Office", desc: 'A portacabin on the lip of a crater. The region.' },
  'commute:digit_13': { district: 'commute', name: 'The Fallen 13', desc: 'A fallen orbital digit, still hot.' },
  'commute:todd_shrine': { district: 'commute', name: 'The Shrine of the First Intern', desc: 'A lawn chair on a bus roof. Todd is in it.' },
  'commute:smiles_hideout': { district: 'commute', name: 'The Overpass Hideout', desc: 'Under a collapsed overpass. A big round shadow.' },
  'commute:missing_texture': { district: 'commute', name: 'The Unfinished Bit', desc: 'A hot zone where the ground is purple and black squares.' },
  // the sims (flashbacks inside the Machine)
  'sims:spire_60': { district: 'sims', name: 'Spire, 60th Floor (16:00)', desc: 'The last workday. Internal Audit. Everybody wants to go home.' },
  'sims:print_room': { district: 'sims', name: 'The Print Room', desc: 'The 60th-floor print room. The tape drive is slow.' },
  'sims:stairwell': { district: 'sims', name: 'Stairwell B', desc: 'Sixty floors of stairs. The sirens start at 17:20.' },
  'sims:lobby': { district: 'sims', name: 'The Lobby (17:29)', desc: 'The doors are right there.' },
  'sims:suburb': { district: 'sims', name: 'Suburb (sim)', desc: 'The training sim the story starts in.' },
  'sims:warehouse': { district: 'sims', name: 'Warehouse (sim)', desc: 'The Warehouse training map. Gary\'s site office is here, and a vending machine that is in no other match.' },
  'sims:school_gate': { district: 'sims', name: 'Hillside Primary (sim)', desc: 'A school gate at 17:30. A sim nobody plays.' },
};
export const LOCATION_IDS = Object.keys(LOCATIONS);
