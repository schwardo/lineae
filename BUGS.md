# Fixed Bugs

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
[x] All submersibles should start at the second from the bottom row.
    - **Fixed**: Changed all submersible starting positions to Y=8.

# Bugs with Questions

[ ] There are 3 mineral spaces on each ocean tile.  Submersibles need to move through each of them, so they each need their own X coordinates.
    - **Question**: Currently the board is 8 wide with 4 deposits. If each deposit needs 6 columns (per the next issue) and there are 3 mineral spaces per ocean tile, this would mean expanding the board to 24 columns (4 deposits × 6 columns)? This is a major structural change. Could you clarify what "3 mineral spaces on each ocean tile" means?

[ ] Each mineral deposit tile has 6 spaces that correspond to each of the mineral columns above it.  Consult the rules to understand how mineral cubes dissolve into the ocean each round.
    - **Question**: The current implementation has 2 columns per deposit (8 board width / 4 deposits). Should the board be 24 columns wide (4 deposits × 6 columns each)? The rules mention "For every mineral column above a mineral deposit tile" but don't specify 6 columns per deposit explicitly. Currently dissolve_minerals adds 2 cubes per deposit per round (which I fixed - it was only adding 1), placing them in the single column at x = deposit_index * 2.

[ ] Pollution cubes can be placed immediately below the Juptier market.  Each pollution cube blocks out 2 electrivity from sunlight for the vessels below it.  Using the diesel engine places a hydrocarbon cube as a pollution cube at any space that the surface vessel could currently move to.  If all possible spaces are full then the diesel engine cannot be used.
    - **Question**: Currently diesel places the hydrocarbon at the vessel's current X position in the atmosphere. Should it instead:
      1. Be placed at ANY reachable X position (where water level is same)?
      2. Block 2 electricity per cube instead of blocking all electricity?
      3. Have multiple atmosphere "layers" below Jupiter for stacking pollution cubes?

# Additional Fix Made

- **dissolve_minerals**: Fixed to add 2 mineral cubes per deposit per round (was only adding 1). The method correctly skips spaces occupied by submersibles or existing resources as per the rules.
