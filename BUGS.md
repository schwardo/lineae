# All Bugs Fixed ✓

## Previously Fixed Bugs

[x] While moving submersibles, there should be no Stay option.
[x] During the sunlight phase, players should gain 6 electricity, not 2, unless the sunlight is blocked by Jupiter.
[x] The display of the ocean board is hard to see.  Draw lines around each space so the grid pattern is more clear, and label the X and Y axis with coordinates.
[x] Use Diesel Engine is not an action that should be available during the Action Phase.  It can only be used during the Sunlight Phase.
[x] Check the starting states of the locks.  There should be 2 open and 2 closed at the start of the game.
[x] At the start of the game, players choose starting locations for their surface vessel and receive the setup resource marked on the mineral deposit tile below them.
[x] Display the state of the mineral deposit tiles, including the set of resources that dissolve into the ocean each round, the setup resource, and the state of the excavation tracks.
[x] When moving their vessels, movement is restricted to spaces at the same ocean height as their current location.
[x] When choosing a destination during vessel movement, tell the player which destinations are valid.
[x] When an invalid destination is selected during vessel movement, the current player should get another chance to make an action.  Currently it goes on to the next player, which is a bug.
[x] Submersibles can hold 4 mineral cubes, not 3.
[x] Also allow lower-case letters to be specified when choosing a submersible.
[x] When displaying the game state, instead of something like "I:2" to indicate two iron cubes just write "I I".  If there are extra spaces that can hold a mineral cube but are not occupied, use "__".  Do this for empty ocean tiles as well.
[x] Instead of one-letter abbreviations for the minerals use the ones written in the rule book (e.g. Fe for Iron).
[x] Mineral deposit tiles have 4 resources:  2 that dissolve into the ocean each round, 1 that you get during excavation, and 1 as a setup bonus.  Display them all appropriately in the Mineral Deposit table.

## Bugs Fixed in This Session

[x] All submersibles should start at the second from the bottom row.
    - Changed all submersible starting positions to Y=8.

[x] There are 3 mineral spaces on each ocean tile.  Submersibles need to move through each of them, so they each need their own X coordinates.
    - Expanded board from 8x10 to 24x9. Each space holds a single mineral cube.

[x] Each mineral deposit tile has 6 spaces that correspond to each of the mineral columns above it.  Consult the rules to understand how mineral cubes dissolve into the ocean each round.
    - Each deposit now controls 6 columns (deposit i controls columns i*6 through i*6+5).
    - The dissolve_minerals method alternates between the primary and secondary resource types across the 6 columns when adding the 2 cubes per round.

[x] Pollution cubes can be placed immediately below the Jupiter marker.  Each pollution cube blocks out 2 electricity from sunlight for the vessels below it.  Using the diesel engine places a hydrocarbon cube as a pollution cube at any space that the surface vessel could currently move to.  If all possible spaces are full then the diesel engine cannot be used.
    - Players can now choose any reachable position (same water level) for pollution placement
    - Each pollution cube blocks 2 electricity (not all electricity)
    - Single atmosphere layer implemented (no stacking)
    - Diesel engine validation checks for available reachable positions

## Additional Improvements

- **dissolve_minerals**: Fixed to add 2 mineral cubes per deposit per round (was only adding 1). The method correctly skips spaces occupied by submersibles or existing resources as per the rules.
- **Board expansion**: Updated all coordinate calculations, display, and game logic to handle the 24x9 board
- **Alternating minerals**: Each deposit has a secondary resource type that alternates with the primary type across its 6 columns
- **Display improvements**: Pollution cubes now show count, deposit positions show range (e.g., "x=0-5")
