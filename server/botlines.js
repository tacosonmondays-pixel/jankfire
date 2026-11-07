// What bots say in chat. {v} = the other person's name, {w} = the weapon. lowercase gamer voice, PG-13, original.
// no apostrophes, quotes or angle brackets: chat goes through clean() like a player's would, and those get stripped
export const LINES = {
  multi: {
    any: ['DOUBLE KILL lmao', 'two for one sale', 'buy one get one free', 'stack em up', 'thats a combo', 'multikill, put it on my resume', 'did yall queue together or', 'clean sweep :3', 'the kill feed is just me now', 'aisle cleared'],
    tryhard: ['ez multi', 'thats why im top frag', 'clip it', 'diff', 'yall are lining up for me', 'my aim is just better sorry'],
    polite: ['oh wow sorry everyone', 'that was lucky haha', 'oops all kills', 'sorry sorry sorry'],
    unhinged: ['THE VOICES SAID DOUBLE', 'i ate two of them XD', 'MORE. MORE.', 'skrrrt', 'i have become the lag', 'mmm kill feed soup'],
    corpo: ['headcount reduced by 2', 'synergy achieved', 'two positions eliminated', 'q4 targets: crushed', 'efficiency up 200 percent'],
  },
  far: {
    any: ['from across the map btw', 'long distance relationship', 'that shot had a layover', 'did you hear that from there', 'shipping included', 'cross map, no map'],
    tryhard: ['hitreg diff', 'thats a 200 iq shot', 'pixel peek kill', 'call me the sniper of the year'],
    polite: ['sorry it was so far away', 'nice dodge almost'],
    unhinged: ['i saw you from SPACE', 'my eyes are telescopes now', 'long boy shot XD'],
    corpo: ['remote work is the future', 'outsourced your death', 'long range planning pays off'],
  },
  head: {
    any: ['DINK', 'right in the thinking spot', 'head check passed', 'skull issue', 'free haircut', 'bonk', 'headshot, no notes'],
    tryhard: ['dome diff', 'cranium collector', 'tap tap', 'aim lab paid off'],
    polite: ['sorry about your head', 'hope that didnt hurt', 'oh no your hat'],
    unhinged: ['brain go bye', 'i collect heads :3', 'ur head is a target and i love targets'],
    corpo: ['upper management removed', 'head of department: gone', 'restructured your head'],
  },
  noscope: {
    any: ['NOSCOPE', 'no scope needed', 'scope? i hardly know her', 'who needs glasses', 'looked away and still hit it', 'mlg pro moment'],
    tryhard: ['360 no scope if i was trying', 'clip that', 'montage material'],
    polite: ['i didnt even aim sorry', 'that was an accident i swear'],
    unhinged: ['my scope is in my heart', 'shot with my eyes closed XD', 'NOSCOPE NOSCOPE NOSCOPE'],
    corpo: ['scope was cut from the budget', 'agile shooting, no planning'],
  },
  revenge: {
    any: ['revenge served', 'remember me', 'thats for earlier', 'payback', 'we are even now', 'what goes around'],
    tryhard: ['you got lucky last time', 'thought so', 'back to normal'],
    polite: ['sorry, had to', 'fair is fair :3'],
    unhinged: ['I NEVER FORGET', 'my grudge is eternal', 'i wrote your name in my notebook'],
    corpo: ['your complaint has been resolved', 'returning your call', 'following up on our last meeting'],
  },
  air: {
    any: ['caught you mid flight', 'airline food is bad', 'pigeon down', 'flight cancelled', 'no landing for you', 'grounded'],
    tryhard: ['air shot diff', 'skeet shooting practice'],
    polite: ['sorry about your trip', 'safe travels'],
    unhinged: ['BIRD', 'i shot a bird', 'fly away little guy XD'],
    corpo: ['your flight has been rescheduled indefinitely', 'travel budget revoked'],
  },
  grapple: {
    any: ['rope privileges revoked', 'cut the cord', 'tarzan down', 'swing and a miss', 'nice rope, mine now'],
    tryhard: ['grapple is not a dodge btw', 'free kill on a rope'],
    polite: ['sorry, you looked so happy up there'],
    unhinged: ['YOINK', 'spiderman? more like spider DEAD XD'],
    corpo: ['your zipline access has expired'],
  },
  clutch: {
    any: ['CLUTCH', 'one v everyone', 'i carried', 'last one standing', 'did yall see that', 'clutch or kick, chose clutch'],
    tryhard: ['team diff but i fixed it', 'thats why im the captain', 'you all owe me'],
    polite: ['we did it team', 'gg team :3', 'phew'],
    unhinged: ['ALONE AND THRIVING', 'i am the whole team now', 'the bomb and i are friends'],
    corpo: ['deliverables delivered', 'i alone hit the kpi', 'promotion please'],
  },
  melee: {
    any: ['hand to hand diff', 'up close and personal', 'personal space violated', 'didnt even need a gun', 'slapped', 'close range customer service'],
    tryhard: ['knife kill, humiliating', 'bring a gun next time'],
    polite: ['sorry for the hug', 'excuse me, coming through'],
    unhinged: ['stab stab :3', 'HUG', 'i just wanted to touch you XD'],
    corpo: ['a hands on approach', 'face to face meeting concluded'],
  },
  goofy: {
    any: ['killed by {w}. look at your life', 'imagine losing to {w}', 'the {w} never misses', '{w} supremacy', 'thats going on the fridge', 'certified goofy kill'],
    tryhard: ['even with {w} i diff you', 'handicap mode and still won'],
    polite: ['sorry it was the {w}', 'the {w} did it, not me'],
    unhinged: ['{w} {w} {w}', 'my {w} is my best friend XD', 'i love my {w} :3'],
    corpo: ['{w} was approved by legal', 'our new product line: {w}'],
  },
  kill: {
    any: ['gg', 'next', 'sit', 'bonk', 'skill issue', 'L', 'ratio', 'too slow', 'get gud', 'cya', 'npc behavior', 'unlucky'],
    tryhard: ['ez', 'sit down', 'you are lagging right', 'uninstall maybe', 'free', 'noob'],
    polite: ['nice try!', 'gg wp', 'you almost had me', 'sorry!!'],
    unhinged: ['XD', 'hehe', 'meow', 'boop', 'nom', 'i am inside your walls (of the map)'],
    corpo: ['you are fired', 'per my last bullet', 'lets circle back never', 'your role has been eliminated', 'please clear your desk'],
  },
  dumb: {
    any: ['lag', 'who put that there', 'my cat jumped on the keyboard', 'that was on purpose', 'controller disconnected', 'i meant to do that', 'ok physics', 'patch notes said that wouldnt happen', 'skill issue (mine)', 'wow'],
    tryhard: ['actual lag', 'my mouse died', 'thats a bug report', 'servers are trash'],
    polite: ['whoops', 'oh no', 'haha oops'],
    unhinged: ['i wanted to see what happens', 'the floor betrayed me', 'WEEEEEE', 'i am free now XD'],
    corpo: ['incident report filed', 'that was a planned outage', 'blaming the intern'],
  },
  died: {
    any: ['lucky', 'ok that was decent', 'nice shot', 'hacks??', 'wait what', 'bruh'],
    tryhard: ['ping diff', 'reported', 'lag', 'you only won cuz i was reloading'],
    polite: ['nice shot!', 'wp', 'good one :3'],
    unhinged: ['i will return', 'ow', 'ouchie', 'respawning angrier'],
    corpo: ['i will be speaking to your manager', 'escalating this', 'noted for my review'],
  },
  gg: {
    any: ['gg', 'ggs', 'gg wp', 'gg go next'],
    tryhard: ['gg ez', 'gg i guess'], polite: ['gg everyone!', 'ggs that was fun :3'], unhinged: ['GG GG GG', 'gooood game XD'], corpo: ['great meeting everyone', 'gg, lets sync next week'],
  },
  ez: {
    any: ['ez? you died like 4 times', 'calm down', 'ez for who', 'the kill feed says otherwise'],
    tryhard: ['you wish', 'ez? check the scoreboard', 'nah'], polite: ['it was close though', 'nice!'], unhinged: ['EZ PZ LEMON SQUEEZY', 'squeezy XD'], corpo: ['lets not overpromise'],
  },
  noob: {
    any: ['who you calling noob', 'takes one to know one', 'says the guy at the bottom', 'mirror'],
    tryhard: ['scoreboard', 'check the kd', 'ok bronze'], polite: ['we all start somewhere :3', 'be nice'], unhinged: ['i AM the noob and i am proud', 'noob noob noob XD'], corpo: ['please keep chat professional', 'hr has been notified'],
  },
  bot: {
    any: ['im not a bot', 'beep boop', 'i have feelings too', 'bot? i passed the captcha', 'i am a real boy'],
    tryhard: ['bot diff'], polite: ['im doing my best!'], unhinged: ['01001000 01001001', 'beep beep XD'], corpo: ['i am a valued contractor'],
  },
  hi: {
    any: ['hi', 'yo', 'sup', 'hello', 'hey hey'],
    tryhard: ['sup'], polite: ['hiii :3', 'hello friend!'], unhinged: ['HELLO', 'hiiiii XD'], corpo: ['good morning team'],
  },
  nice: {
    any: ['ty', 'thanks', 'i know', 'thx :3'],
    tryhard: ['obviously'], polite: ['thank you!!'], unhinged: ['NICE NICE NICE'], corpo: ['appreciate the feedback'],
  },
  // zombies: the squad's bots (server/zmbots.js)
  zmhi: {
    any: ['squad up', 'i brought snacks', 'which way are the zombies', 'ok im here, where is the gun wall', 'reporting for zombie duty'],
    tryhard: ['dont worry i got this', 'i will carry, stay behind me'], polite: ['hi team!! lets do our best :3', 'nice to meet you all'], unhinged: ['I HAVE BEEN WAITING FOR THIS', 'i love the smell of zombie in the morning'], corpo: ['onboarding complete', 'happy to join this initiative'],
  },
  zmleave: {
    any: ['ok {v} you can have my spot', 'my mom is calling, {v} take over', 'tagging out, {v} is in', 'gotta go feed my cat, good luck {v}', 'this is where i get off. go {v}', 'ok i lagged out on purpose. {v} has the controls'],
    tryhard: ['fine, {v} can try to fill my shoes', 'leaving before i carry too hard'], polite: ['bye everyone!! {v} take care of them :3', 'sorry, gotta go! welcome {v}'], unhinged: ['I MUST RETURN TO THE VOID. {v} INHERITS MY CREDITS. not really', 'goodbye forever (5 minutes)'], corpo: ['handing off to {v}, see the doc', 'my contract has ended. {v} is the new hire'],
  },
  zmdown: {
    any: ['IM DOWN', 'help im on the floor', 'revive meeee', 'i am horizontal', 'someone pick me up', 'floor time again'],
    tryhard: ['lag. revive me', 'that was not my fault'], polite: ['sorry, could someone help me up', 'oops im down, sorry!'], unhinged: ['the floor is nice actually', 'IM A RUG NOW'], corpo: ['requesting immediate support', 'escalating: i am on the ground'],
  },
  zmrevive: {
    any: ['up you get {v}', 'got you {v}', 'no dying on my watch', 'stand up {v}, we have work', 'revived, thats 10 bucks'],
    tryhard: ['carried you again {v}', 'you owe me one {v}'], polite: ['there you go {v}!! careful :3', 'are you ok {v}?'], unhinged: ['RISE {v} RISE', 'i put your soul back in, mostly'], corpo: ['{v} has been reinstated', 'back to work {v}'],
  },
  zmthanks: {
    any: ['ty {v}', 'thanks {v}', 'ok i owe you', 'saved by {v}', 'back in the game'],
    tryhard: ['i was about to get up anyway'], polite: ['thank you so much {v}!!', 'youre the best {v} :3'], unhinged: ['{v} I WOULD DIE FOR YOU. again'], corpo: ['thank you {v}, noted for your review'],
  },
  zmbuy: {
    any: ['bought the {w}', 'new toy: {w}', '{w} acquired', 'shopping spree', 'cha ching, {w}'],
    tryhard: ['{w}, best gun on the wall', 'ok now its fair: {w}'], polite: ['i got the {w}, hope thats ok', 'look, a {w}!'], unhinged: ['THE {w} SPOKE TO ME', 'i licked the {w}'], corpo: ['procured one (1) {w}', '{w} expensed to the company'],
  },
  zmmach: {
    any: ['gambling time', 'feed the machine', 'lets go cheats', 'come on come on come on', 'one more spin'],
    tryhard: ['rolling for the best one'], polite: ['i hope i get a good one!'], unhinged: ['THE MACHINE HUNGERS', 'i gave it my lunch money and my soul'], corpo: ['investing in synergy', 'high risk, high reward'],
  },
  zmround: {
    any: ['round {v} done', 'still alive lol', 'is that all they got', 'another one down', 'board the windows guys'],
    tryhard: ['too easy, next', 'round {v}, i did most of it'], polite: ['good job team!!', 'we did it, round {v}!'], unhinged: ['MORE ZOMBIES. I NEED MORE', 'round {v} and i can taste colours'], corpo: ['round {v} closed on schedule', 'quarterly zombie targets: met'],
  },
};

// personalities: how chatty (a multiplier on every chance) and how salty they are when they die
export const PERSONAS = {
  tryhard: { talk: 1.3, salt: 1.4 },
  polite: { talk: 1, salt: 0.6 },
  unhinged: { talk: 1.5, salt: 1 },
  corpo: { talk: 1, salt: 0.9 },
  silent: { talk: 0.15, salt: 0.2 },
};
export const PERSONA_IDS = Object.keys(PERSONAS);

// replies to a player's chat: the first pattern that matches picks the pool
export const REPLY = [
  [/\b(gg|ggs|good game|gg wp)\b/i, 'gg'],
  [/\b(ez|easy|ezz+|too easy)\b/i, 'ez'],
  [/\b(noob|nub|newb|bad|trash|garbage)\b/i, 'noob'],
  [/\b(bot|bots|npc|ai)\b/i, 'bot'],
  [/\b(nice|ns|nt|wp|good shot)\b/i, 'nice'],
  [/^(hi|hey|hello|yo|sup|hii+)\b/i, 'hi'],
];
