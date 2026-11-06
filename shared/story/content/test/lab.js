// The story lab: test content for the WP8 engine on the Training range (until the Bottom and the Gut exist).
// A 3-step quest with a branch, a branching conversation, codex entries, and one scene of each kind.
// Spots here are offsets from where you spawn ([x, y, z], dropped onto the floor), because the range is a test map.
export const anchor = 'spawn';

export const npcs = {
  lumps: {
    id: 'lumps', name: 'LUMPS', title: 'the muscle. cries at sunsets', look: 'lumps', voice: { kind: 'tuba', pitch: 0.55, rate: 0.8 },
    home: { p: [-4, 0, 6], face: 2.4 }, idle: 'sway', cam: 'closeup',
    lines: {
      start: { go: [['q.lab_soup.done', 'after'], ['q.lab_soup.active', 'busy']],
        say: ['...', 'oh. hello. i didn\'t see you there. i was looking at the sky.', 'it does a colour at the end of the day. i always miss it.'],
        opts: [['you okay, big guy?', 'sad'], ['need anything?', 'soup'], ['bye', 'bye']] },
      sad: { say: ['i\'m fine. i\'m just big on the outside.', '*he wipes his eye with a forearm the size of a fridge*'], opts: [['need anything?', 'soup'], ['bye', 'bye']] },
      soup: { say: ['soup. auntie needs the pot of soup. the red kind.', 'the pot\'s by the ledge. don\'t let the interns have it.'], face: 'grin',
        do: ['quest.start:lab_soup', 'codex:lore.soup'], opts: [['on it', 'bye']] },
      busy: { say: ['the soup. please. auntie gets grumpy when she\'s hungry.', 'grumpier.'] },
      after: { say: ['you did the soup. you\'re my friend now. that\'s how it works.'], again: ['friend.'] },
      bye: { say: ['bye. look at the sky sometimes.'] },
    },
  },
  gordo: {
    id: 'gordo', name: 'WEE GORDO', title: 'the planner. small, sharp', look: 'gordo', voice: { kind: 'kazoo', pitch: 1.5, rate: 1.25 },
    home: { p: [5, 0, 7], face: -2.4 }, idle: 'fidget',
    lines: {
      start: { go: [['flag.bribedGordo', 'paid'], ['flag.braveSoup', 'brave2']],
        say: ['what.'], opts: [['lumps sent me. soup business.', 'sent', { if: 'q.lab_soup.active' }], ['what\'s your deal?', 'deal'], ['nothing. bye', 'bye']] },
      deal: { say: ['my deal is the spire comes down. no deals. no new bosses. just a big hole where it was.', 'next question.'],
        do: ['codex:lore.spire'], opts: [['noted', 'bye']] },
      sent: { say: ['the interns are camping the soup. i could call them off.', 'for a price. i\'m not a charity. i\'m a planner.'],
        opts: [['here. keep them off me.', 'bribe', { do: ['flag:bribedGordo', 'standing:bottom-2', 'coupons:-20'] }], ['i\'ll fight them myself.', 'brave', { do: ['flag:braveSoup', 'standing:bottom+2'] }]] },
      bribe: { say: ['pleasure doing business. they\'re gone. go.'], face: 'grin', do: ['codex:frag.option_c_1'] },
      brave: { say: ['brave. dumb. same thing round here.'] },
      paid: { say: ['we\'re square. don\'t make it weird.'] },
      brave2: { say: ['still alive? huh.'] },
      bye: { say: ['mm.'] },
    },
  },
  auntie: {
    id: 'auntie', name: 'AUNTIE SPREADSHEET', title: 'keeps the books in crayon', look: 'auntie', voice: { kind: 'crayon', pitch: 1.1, rate: 0.9 },
    home: { p: [0, 0, 11], face: Math.PI }, idle: 'write',
    lines: {
      start: { go: [['q.lab_soup.at.deliver && has.soup_pot', 'deliver'], ['q.lab_soup.done', 'after']],
        say: ['i\'m doing the books. the books are doing me.'], opts: [['what happened to the world?', 'world'], ['bye', 'bye']] },
      world: { say: ['the companies ended it. on purpose. on a tuesday.', 'sixty-one years ago. you hungry?'], do: ['codex:lore.final_quarter'] },
      deliver: { say: ['is that soup? the red kind?', '*she writes SOUP: 1 in crayon, then underlines it twice*'], face: 'grin' },
      after: { say: ['thank you for the soup. it\'s in the books now. in crayon, so it\'s forever.'] },
      bye: { say: ['mind the knee.'] },
    },
  },
  dale: {
    id: 'dale', name: 'DALE', title: 'fixes the machine', look: 'dale', voice: { kind: 'grumble', pitch: 0.85, rate: 0.85 },
    home: { p: [-6, 0, 12], face: 2.0 }, idle: 'idle',
    lines: { start: { say: ['she never gave anything. forty years.', 'then she gave change.'], opts: [['who\'s change?', 'you'], ['bye', 'bye']] },
      you: { say: ['you. you\'re change.'], face: 'squint' }, bye: { say: ['*he hits a machine that isn\'t there*'] } },
  },
  clerk: {
    id: 'clerk', name: 'TEMP #22', title: 'a ☺ CORP temp. smiling (painted on)', look: 'mannequin', voice: { kind: 'beep', pitch: 1.3, rate: 1 },
    home: { p: [2, 0, 3], face: Math.PI }, idle: 'idle', walk: { loop: [[2, 0, 3], [6, 0, 3], [6, 0, -1], [2, 0, -1]], speed: 1.4 },
    lines: { start: { say: ['have a punctual day.', 'have a punctual day.'], again: ['have a punctual day.'] } },
  },
};

export const zones = {
  'lab:pot': { p: [-1.5, 0, 9], r: 1.6, name: 'the soup pot' },
  'lab:ledge': { p: [0, 0, 12], r: 6 },
};

// things you can pick up / use (the host draws them and sends pickup / interact events)
export const things = {
  soup_pot: { zone: 'lab:pot', item: 'soup_pot', name: 'SOUP POT', look: 'pot', if: 'q.lab_soup.at.pot' },
};

export const quests = {
  lab_soup: {
    id: 'lab_soup', title: 'SOUP TEST', giver: 'lumps', act: 1, kind: 'main', blurb: 'auntie needs the red soup. the interns want it too.',
    steps: [
      { id: 'pot', text: 'grab the soup pot', goal: { type: 'pickup', item: 'soup_pot', zone: 'lab:pot', marker: 'lab:pot' } },
      { id: 'interns', text: 'deal with the interns', any: true, goals: [
        { type: 'kill', kind: 'dummy', n: 2, text: 'bonk 2 interns' },
        { type: 'flag', flag: 'bribedGordo', text: 'or pay wee gordo to call them off', marker: 'gordo', to: 'sneak' },
      ] },
      { id: 'deliver', text: 'bring the soup to auntie (don\'t spill it)', timer: 120, failText: 'the soup went cold', failTo: 'deliver',
        fail: { type: 'flag', flag: 'soupSpilled' }, goal: { type: 'deliver', item: 'soup_pot', to: 'auntie' }, next: 'end:fought' },
      { id: 'sneak', text: 'sneak the soup to auntie', goal: { type: 'deliver', item: 'soup_pot', to: 'auntie' }, next: 'end:bribed' },
    ],
    ends: { fought: { grade: 'EXCEEDS EXPECTATIONS', do: ['flag:soupHero'] }, bribed: { grade: 'MEETS EXPECTATIONS', do: ['flag:soupDeal'] } },
    reward: { coupons: 300, flags: ['lab_done'], standing: { bottom: 5 }, codex: ['frag.option_c_2'] },
    scenes: { start: 'lab_panels', end: 'lab_moment' },
  },
};

export const codex = {
  'lore.soup': { kind: 'lore', title: 'THE RED SOUP', text: 'the bottom trades soup to gristle & sons for medicine. nobody asks what\'s in either.' },
  'lore.spire': { kind: 'lore', title: 'THE ☺ SPIRE', text: 'the only lit building in the dark. wee gordo wants it gone.' },
  'lore.final_quarter': { kind: 'lore', title: 'THE FINAL QUARTER', text: '16:59 on the last afternoon of Q4, six boards signed option c. 17:30, the launch.' },
  'frag.option_c_1': { kind: 'frag', title: 'OPTION C (1/6)', text: '"...in the event of a sustained loss of market share, the board may elect to..."' },
  'frag.option_c_2': { kind: 'frag', title: 'OPTION C (2/6)', text: '"...the workforce shall be retained in an archival format..."' },
  'char.lumps': { kind: 'char', title: 'LUMPS', text: 'the bottom\'s muscle. gigantic forearms, small head, cries at sunsets.' },
  'char.gordo': { kind: 'char', title: 'WEE GORDO', text: 'the bottom\'s planner. wants the spire burned down.' },
  'char.auntie': { kind: 'char', title: 'AUNTIE SPREADSHEET', text: 'agnes pell. ex-☺ CORP auditor. runs the lost & found. keeps the books in crayon.' },
  'char.dale': { kind: 'char', title: 'DALE', text: 'fixes the machine. let you out.' },
  'char.clerk': { kind: 'char', title: 'TEMP #22', text: 'a temp. the smile is painted on.' },
};

export const scenes = {};
