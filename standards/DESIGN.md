# Design with no opinion per page

How an agent judges a look with no person. Principle S2 of `PRINCIPLES.md`. The owner, 2026-11-13: one look at a
design system is possible, a check of each place is not.

## The rules

1. **One design system per project.** A project with a user interface has tokens (colors, fonts, space, radius) and
   one style page that shows each component in each state. The agents make the style page from the code of the
   product, so the page cannot differ from the product.
2. **The owner approves it one time.** The approval is a proposal card with the address of the style page.
   A later change of a token or of a component rule is a new proposal card. A use of the system needs no approval.
3. **Machines judge each change.** After the approval, a change of a screen passes these checks with no person:
   - a lint that refuses a color, a font or a distance that is not a token;
   - screenshots at phone width and at desktop width, with a pixel comparison against the approved state. A change
     that is intended updates the approved state in the same PR, and the PR shows before and after;
   - accessibility checks;
   - layout rules: touch targets, no sideways scroll, a visible focus;
   - a review by a model against the style page, with a fixed list of points. The result goes into the PR.
4. **A design from a reference.** When a thing must look like a reference (aoe2mc: a building must look like the
   game), the agent gets the reference image, renders the design from fixed views, and compares. A look score from an
   image model replaces the difference list "by eye" when it exists (roadmap `design:systems`).
5. **A new project** starts from the base of the fleet with a theme of its own (roadmap `projects:house-stack`).
   Then the owner approves the base one time for all projects.

## The state of the projects on 2026-11-13

| Project | It has | It does not have |
|---|---|---|
| aoe2mc | Reference images, renders from two sides, a difference list in each PR | A look score |
| travel-aggregator | Tokens in `DESIGN.md`, look tests at two widths, screenshots in CI | A token lint, a pixel comparison, an approved style page |
| tumach-dance | CSS variables for the tokens, a look test, accessibility checks, speed budgets | A token lint, a pixel comparison, an approved style page |

No project has an approval of its design system by the owner yet. The roadmap feature `design:systems` brings each
project to rules 1 to 3.
