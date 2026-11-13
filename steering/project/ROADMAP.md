# Roadmap

The goals of street-quiz and their features: done (`[x]`) or missing (`[ ]`). The `roadmap` skill makes the next epic from a missing feature.

## 1. Learn the streets of an area

- [ ] `area:skeleton` One small area that is in the app, on a map with no street names: the app marks a street and you type its name
  - The app runs on a phone from its public address, with no account
  - A right answer and a wrong answer look different, and the next street comes
- [ ] `area:draw` You draw a shape on the map with a finger, and the app takes each street with a name inside the shape
  - You can scroll and zoom the map before and after you draw
  - The parts of one street count as one street
  - The street data comes from OpenStreetMap and stays on the device for the next visit
- [ ] `area:choices` Answer with four options in place of typing
  - Easy: the wrong options are random streets of the area
  - Hard: the wrong options are streets near the marked street
- [ ] `area:tap` The other direction: the app gives a name and you tap the street on the map
  - A tap near the street counts, and the app shows the correct street after a wrong tap
- [ ] `area:typing` A typed answer that is almost correct counts
  - Capital letters, accents and a short form such as "str." do not make an answer wrong
- [ ] `area:progress` The app remembers what you know
  - A street that you missed comes back sooner than a street that you know
  - Each area shows how many of its streets you know
- [ ] `area:prove` A proof round: each street of the area one time, with a result at the end
  - The result shows the score and the streets that you missed
- [ ] `area:saved` More than one area, each with a name of yours
  - You can switch between areas, change a name and remove an area

## 2. Learn the large streets of a city

- [ ] `rank:formula` The app ranks the streets of an area from large to small
  - The rank uses values from OpenStreetMap: the length of the street, its road class and its number of lanes
  - A long quay with little traffic does not rank above a main street
- [ ] `rank:levels` Three levels select how many streets you learn: easy, medium and hard
  - Easy has only the largest streets, and each next level adds smaller streets
  - A level shows its number of streets before you start
- [ ] `rank:city` Select a city or a town by its name in place of a shape
  - "The 100 largest streets of Amsterdam" is one selection
- [ ] `rank:why` Each street shows why it is in its level
- [ ] `rank:exclude` Remove a street that does not belong to your selection
  - A removed street stays out of the quiz and out of the score of that area

## 3. Learn the streets of a route

- [ ] `route:ab` Give a start and an end, with stops between them: the app makes a route and you learn its streets
  - The route follows roads, and the quiz has the streets in the sequence of the route
- [ ] `route:extended` An "extended" switch adds the side streets of the route
- [ ] `route:next` A quiz that asks for the next street of the route

## 4. A good app on each phone

- [ ] `app:offline` The app and a saved area work with no internet
- [ ] `app:languages` The texts of the app are in English and Dutch
- [ ] `app:share` Share an area or a route with a link, and the other person gets the same streets
- [ ] `app:feedback` A feedback button sends what you saw and what you did (the feedback standard of the fleet)
