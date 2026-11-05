# Profesora: League of Legends topics (Shorts of 1 to 3 minutes)

Every fact was checked on the official LoL wiki (wiki.leagueoflegends.com) on 2026-11-04.
If a patch changes one of them, check it again before recording.

| # | Title / hook | Verified fact the class is built on | Map | Status |
|---|---|---|---|---|
| 1 | **"¿Por qué te pega toda la oleada?"** | When you hit an enemy champion, its nearby minions (~500 units) switch to you. Minions do 60% of their damage against champions. They follow a 6-level priority list and only switch target when a higher priority appears. | bottom lane | **episodes/01 (in production)** |
| 2 | **"¿Por qué la torre te elige a ti?"** | A turret attacks the first enemy that enters its range (750) and stays on it until it dies, unless you hurt an allied champion within 1400. Warming Up: +50% per hit up to +150% bonus, resets after 5 s, not on a target switch. Reinforced Armor: -80% damage taken with no enemy minions nearby. | bottom lane + turret | **episodes/02 (in production)** |
| 3 | **"¿Cuántos disparos de torre aguanta cada súbdito?"** (farming under turret) | The turret takes a fixed % of the minion's max health per shot: melee 45% (3 shots), caster 70% (2), siege 14% (8), super 5% (20). Teaches which last hits to set up with your own basic attack. | mid lane | idea |
| 4 | **"El cerebro de un súbdito"**: the full priority list, as an exam | 1) enemy champion attacking an allied champion, 2) enemy minions attacking an allied champion, 3) enemy minions attacking an allied minion, 4) enemy turrets attacking an allied minion, 5) closest minion, 6) closest champion. Targets are re-evaluated between attacks. | any | idea |
| 5 | **"El arbusto no te hace invisible para siempre"** | Units inside brush are hidden until sight is granted over it. Targeted attacks and abilities reveal you in a 300 radius for 2 seconds. | brush close-up | idea |
| 6 | **"¿Por qué te cortan el recall?"** | Recall: 0.5 s cast + 8 s channel. Empowered Recall: 4 s. Damage interrupts it (except in the last 0.1 s, or if a shield absorbs it), and so do stuns, silences, knock-ups, grounds and roots. | base / lane | idea |
| 7 | **"El reloj de las oleadas"** | Waves from 00:30 every 30 s; from 14:00 every 25 s; from 30:00 every 20 s. The siege minion first appears in wave 3 (01:30), then every 3 waves until 14:00, every 2 after that, and every wave from 25:00. It doesn't spawn in waves with super minions. | lane + clock | idea |
| 8 | **"El alma del dragón explicada en 1 minuto"** | The first team to 4 drakes gets the Soul. The first two drakes are different elements; after that the rift's dominant element repeats. Once there's a Soul, the Elder appears: +Aspect of the Dragon for 150 s, lost on death. | river / pit | idea |
| 9 | **"¿Por qué no puedes hacer backdoor?"** | Reinforced Armor: turrets take 80% less damage (even true damage) with no enemy minions or summoned Herald nearby. Pairs well with an episode on "when to push". | turret | idea |
| 10 | **"Las placas de torre: oro escondido"** | Outer lane turrets have 5 plates; each one grants 120 local gold. The turret gains Bulwark stacks as it loses health. *(Before recording: confirm whether the plates still drop at 14:00 in the current patch; the wiki shows conflicting notes.)* | turret | idea (check patch) |
| 11 | **"Experiencia compartida: por qué conviene estar cerca"** | Patch 26.01: solo minion XP went to 100% (from 95%) and shared XP to 130% (from 124%). Explains why 2 people in a lane level up more slowly. | bottom lane | idea (check the current numbers) |
| 12 | **"Mitos de la profe"**: 3 common mistakes in 90 s | Myth: "the turret attacks whoever is nearest" (false: the first one that enters). Myth: "hitting a minion makes everyone come at you" (false: the alarm is triggered by hitting a champion). Myth: "if you switch target, the turret cools down" (false: Warming Up doesn't reset on a target switch). | mixed | idea (recap of 1 and 2) |

## Sounds
Every episode marks its "sound slots" (basic attack, ability, minion death, turret shot, gold...).
For now they use effects from our library (`C:\videos-youtube\sfx`). Once the real game sounds are extracted, they go into
`C:\videos-youtube\league\assets\sfx\` and the `C:\videos-youtube\league\motor\sonidos.json` map gets updated. Nothing else needs to be touched.

## Required description (Riot policy)
"[Title] was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project."
No Riot logos, and no Riot trademarks used as tags.
