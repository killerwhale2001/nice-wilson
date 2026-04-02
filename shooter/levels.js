import { Sentinel, Vortex, Leviathan } from './entities.js';

export const LEVELS = [
  {
    // Level 1: Drifters + Trackers only
    waves: [
      { enemies: [{ type: 'Drifter', count: 6  }],                                                spawnInterval: 60 },
      { enemies: [{ type: 'Drifter', count: 6  }, { type: 'Tracker', count: 3 }],                 spawnInterval: 55 },
      { enemies: [{ type: 'Drifter', count: 5  }, { type: 'Tracker', count: 5 }],                 spawnInterval: 50 },
      { enemies: [{ type: 'Drifter', count: 8  }, { type: 'Tracker', count: 6 }],                 spawnInterval: 45 },
    ],
    bossClass: Sentinel,
  },
  {
    // Level 2: Add Shooters
    waves: [
      { enemies: [{ type: 'Drifter', count: 6 }, { type: 'Tracker', count: 4 }, { type: 'Shooter', count: 2 }], spawnInterval: 50 },
      { enemies: [{ type: 'Tracker', count: 6 }, { type: 'Shooter', count: 4 }],                                spawnInterval: 45 },
      { enemies: [{ type: 'Drifter', count: 8 }, { type: 'Shooter', count: 4 }],                                spawnInterval: 45 },
      { enemies: [{ type: 'Tracker', count: 6 }, { type: 'Shooter', count: 6 }, { type: 'Drifter', count: 4 }], spawnInterval: 40 },
    ],
    bossClass: Vortex,
  },
  {
    // Level 3: Add Splitters, max density
    waves: [
      { enemies: [{ type: 'Drifter', count: 8  }, { type: 'Splitter', count: 3 }],                                                                                     spawnInterval: 45 },
      { enemies: [{ type: 'Tracker', count: 6  }, { type: 'Shooter', count: 4 }, { type: 'Splitter', count: 3 }],                                                       spawnInterval: 40 },
      { enemies: [{ type: 'Splitter', count: 5 }, { type: 'Shooter', count: 5 }],                                                                                      spawnInterval: 40 },
      { enemies: [{ type: 'Drifter', count: 8  }, { type: 'Tracker', count: 6 }, { type: 'Splitter', count: 4 }, { type: 'Shooter', count: 4 }],                        spawnInterval: 35 },
    ],
    bossClass: Leviathan,
  },
];
