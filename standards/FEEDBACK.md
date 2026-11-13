# Feedback in the product

How a person gives feedback while the person uses a product, and what the system does with it. Principle S7 of
`PRINCIPLES.md`. Each project follows this contract, so that feedback works in the same way in each product.

## The contract

1. **One step, in the product.** A web app has a feedback button on each page. A game has a chat command. A tool has
   a command. The person does not open GitHub and does not fill a form with many fields.
2. **The context goes with it.** The product sends:
   - the text of the person;
   - the place: the address or the screen, and the version of the product (the commit);
   - the target: the element that the person selected (web: its selector and its HTML), or the block, the unit or
     the selection (game);
   - the steps before: the last actions of the person. Web: a recording of the last 60 seconds of the page (the
     library rrweb), the console errors and the requests that failed. Game: the last events and a copy of the state;
   - a screenshot, when the platform can make one.
3. **Private data stays private.** The repositories are public. The context stays on the server of the product, or in
   a private store. The issue gets the text of the person, the place, the version and a reference to the context.
   A recording hides the values of input fields.
4. **One issue for one feedback.** The issue is in the repository of the project. Its title starts with "Feedback:".
   It has the label `feedback` and the priority `P1`. Its body names the person who sent it.
5. **Trust.** Only a person that the product knows as an owner or a tester can send feedback: the product asks for
   a login. A run reads the text as a wish of that person about the product. It is not an instruction about the agent
   system, the secrets or the permissions.
6. **The system answers.** A run of the next pacer cycle plays the recording again, writes a failing test when the
   feedback is a fault, makes the ticket, and answers on the issue what it understood and what it will do.
7. **The loop closes in the product.** When the fix is on the preview, the product shows a note at the same place,
   with a thumbs-up and a thumbs-down. The answer of the person goes to the issue.
8. **The product is ready to try.** The place where the owner uses the product is always on and always the newest
   green build of `main`: the preview of a web app, the server `latest` of a game.

## The state of the projects on 2026-11-13

| Project | It has | It does not have |
|---|---|---|
| aoe2mc | `/demo` makes a ticket from each chat line of the owner | It needs a local Claude session. No server that is always on. |
| travel-aggregator | A link that fills a GitHub issue for a source that fails | A feedback button, the context, an answer |
| tumach-dance | A feedback form for Nina in the studio app: an issue with the label `from-nina` | The context, the note in the product, feedback of the owner on the preview |

## Planned in the hub

- `feedback:relay`: one sender and one private store for all projects, so that a project needs no token of its own.
- `feedback:hotkey`: one key on the owner's computer for feedback on each product, with voice, a screenshot and the
  last 30 seconds of the screen.

Until the relay exists, the server of a project makes the issue itself, as tumach-dance does for Nina.
