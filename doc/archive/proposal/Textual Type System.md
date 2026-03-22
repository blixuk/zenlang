# Textual Type System Proposal

## High-Level Concept

Instead of treating strings as just arrays of characters, ZenLang treats them as semantic text structures:

- Character → A single Unicode glyph
- Word → A sequence of Characters
- Sentence → A sequence of Words, seperated by a space
- Paragraph → A sequence of Sentences
- Chapter → A sequence of Paragraphs
- Book → A sequence of Chapters
This allows ZenLang to:
- Provide richer API operations
- Enforce readability rules or formatting rules if the user wants
- Build powerful text manipulation tools
- Offer domain-specific use cases like script-writing, storytelling, documentation systems, etc.

## Syntax Proposal

### Characters

let c : Character = `A`
let c = `A`


### Words

let w : Word = `Hello`
let w = `Hello`

w.characters() // returns a list of the Characters in the Word
w.length() // returns the amount of Characters in the Word

w[0] // returns the Character at that index
w.get(0) // returns the Character at that index

w[1] = `a` // sets the Character at that index
w.set(`a`) // sets the Character at that index


### Sentences

let s : Sentence = `Hello Word`
let s = `Hello Word`

s.words() // returns a list of the Words in the Sentence
s.length() // returns the amount of Words in the Sentence

s[0] // returns the Word at that index
s.get(0) // returns the Word at that index

s[1] = `There` // sets the Word at that index
s.set(`There`) // sets the Word at that index


### Paragraphs

let p : Paragraph = ```
Hello Word
This is a test
```
let p = ```
Hello Word
This is a test
```

p.sentences() // returns a list of the Sentences in the Paragraph
p.length() // returns the amount of Sentences in the Paragraph

p[0] // returns the Sentence at that index
p.get(0) // returns the Sentence at that index

p[1] = `Good to see you` // sets the Sentence at that index
p.set(`Good to see you`) // sets the Sentence at that index

### Chapters

let c : Chapter = {
```
Hello Word
This is a test
```

```
This is anothher Paragraph
It is very good.
```
}

let c = {
```
Hello Word
This is a test
```

```
This is anothher Paragraph
It is very good.
```
}

c.paragraphs() // returns a list of the Paragraphs in the Chapter
c.length() // returns the amount of Paragraphs in the Chapter

c[0] // returns the Paragraph at that index
c.get(0) // returns the Paragraph at that index

c[1] = ```
Good to see you
This is a new Paragraph!
``` // sets the Paragraph at that index

c.set(```
Good to see you
This is a new Paragraph!
```) // sets the Paragraph at that index

` `
`` ``
``` ```
```` ````

c` `
w` `
s` `
p` `
