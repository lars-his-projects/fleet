# Principles

The direction of street-quiz, made from the owner's decisions (`steering/project/DECISIONS.md`).
The runs add a principle when the owner decides a question (the `ticket` skill, "Decision tickets"). Agents: before
you recommend an option, compare it with these principles and name the principle ("follows P1").

## P1. A flashcard, not a trivia game

The questions are plain: the name of a marked street, or the street of a given name. The app asks no question about
history or facts. Example: the quiz never asks who a street is named after.

## P2. A real map

The user scrolls and zooms a real map. A street is a shape on the map from OpenStreetMap, not a picture with fixed
pixels. The names on the map stay hidden during a quiz.

## P3. Open data and free services

The map and the streets come from OpenStreetMap. The app uses no paid service and no key in the browser. A service
with a cost or a key needs a decision ticket. Obey the usage policy of each free service: keep the data on the device,
and send no request to a map or data service from CI or from a cloud session. Tests use stored data.

## P4. Phone first, no account

The app works on a phone with one hand. The progress stays on the device. The app has no login and no server of its own.

## P5. The user can see how streets are selected

A formula with values from OpenStreetMap decides which streets are large. The app shows these values, and the user can
remove a street from a selection.

## Owner involvement

The areas where the owner decides each choice, also when one option is clearly best (a decision ticket). In all
other areas the agents decide, and ask only when two options are equally good.

- Only real ties.
- The look follows the design standard of the fleet: one design system, approved one time.

## Try a feature

How the owner tries a new feature. The agents make what this needs for each feature or epic.

- A live preview: each merge to `main` goes to GitHub Pages (https://lars-his-projects.github.io/street-quiz/). The
  owner opens it on a phone. The first roadmap feature makes the deploy workflow.
