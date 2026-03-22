
Primitive Types:
Vector: Static Array
List: Dynamic Array

String: Dynamic Array of bytes (UTF-32 default encoding, utf-8 optional)
String could be built on top of the List Type

String            // UTF-32 default encoding
String[Encoding]  // Size of the encoding in bytes
String[8]         // UTF-8 encoding
String[16]        // UTF-16 encoding
String[32]        // UTF-32 encoding

`A`
`Hello`
`Hello World`
`This is a simple string`

Abstract Types:
Text: Takes any String Type


# Textual Type System Proposal

Zenlang will use the String Type as the base type for text. Zenlang will treat Strings as streams for writing and reading text like the unix shell.

Strings are just arrays of bytes and a Character is just a String of length 1.
This removes the need for a separate 'Character' primitive type, simplifying the language model. No more need for 'Rune' or 'Char' types.

## High-Level Concept

Instead of treating strings as just Dynamic Arrays of bytes, ZenLang treats them as semantic text structures.

The following are the Abstract text types:
- Glyph:        A single Unicode glyph (A String of length 1)
- Word:         A sequence of Glyphs (A String of length 2 or more)
- Sentence:     A sequence of Words, separated by a space
- Paragraph:    A sequence of Sentences
- Chapter:      A sequence of Paragraphs
- Book:         A sequence of Chapters

This allows ZenLang to:
- Provide richer API operations
- Enforce readability rules or formatting rules if the user wants
- Build powerful text manipulation tools
- Offer domain-specific use cases like script-writing, storytelling, documentation systems, etc.

## Syntax Proposal

### Glyph

let g : Glyph -> `A`
let g -> [G]`A`
let g :> [G]`A`

g.bytes     // return the bytes of the Glyph
g.codepoint // return the codepoint of the Glyph

g -> [G]`B`

### Word

let w : Word -> `Hello`
let w -> [W]`Hello`
let w :> [W]`Hello`

w.glyphs      // returns a list of the Glyphs in the Word
w.length      // returns the amount of Glyphs in the Word

w[0]          // get the Glyph at that index
w.get(0)      // get the Glyph at that index

w[1] -> [G]`a`   // set the Glyph at that index
w.set([G]`a`)    // set the Glyph at that index

### Sentence

let s : Sentence -> `Hello Word`
let s -> [S]`Hello Word`
let s :> [S]`Hello Word`

s.words       // returns a list of the Words in the Sentence
s.length      // returns the amount of Words in the Sentence

s[0]          // get the Word at that index
s.get(0)      // get the Word at that index

s[1] -> `There` // set the Word at that index
s.set(`There`) // set the Word at that index

### Paragraph

let p : Paragraph -> `
Hello Word
This is a test
`

let p -> [P]`
Hello Word
This is a test
`

let p -> [P]`
[S]`Hello Word`
[S]`This is a test`
`

p.sentences    // returns a list of the Sentences in the Paragraph
p.length       // returns the amount of Sentences in the Paragraph

p[0]           // get the Sentence at that index
p.get(0)       // get the Sentence at that index

p[1] -> [S]`Good to see you` // set the Sentence at that index
p.set([S]`Good to see you`)  // set the Sentence at that index

### Chapter

let c : Chapter -> {
[P]`
Hello Word
This is a test
`,
[P]`
This is another Paragraph
It is very good.
`
}

let c -> {
[P]`
Hello Word
This is a test
`,
[P]`
This is another Paragraph
It is very good.
`
}

c.paragraphs    // returns a list of the Paragraphs in the Chapter
c.length        // returns the amount of Paragraphs in the Chapter

c[0]            // get the Paragraph at that index
c.get(0)        // get the Paragraph at that index

c[1] -> [P]`
Good to see you
This is a new Paragraph!
` // set the Paragraph at that index

c.set(
[P]`
Good to see you
This is a new Paragraph!
`
) // set the Paragraph at that index


### Book

let b : Book -> {
[C]{
[P]`
Hello Word
This is a test
`,
[P]`
This is another Paragraph
It is very good.
`
},
[C]{
[P]`
Hello Word
This is a test
`,
[P]`
This is another Paragraph
It is very good.
`
}
}

let b -> [B]{
[C]{
[P]`
Hello Word
This is a test
`,
[P]`
This is another Paragraph
It is very good.
`
}
}

b.chapters    // returns a list of the Chapters in the Book
b.length      // returns the amount of Chapters in the Book

b[0]          // get the Chapter at that index
b.get(0)      // get the Chapter at that index

b[1] -> [C]{
[P]`
Good to see you
This is a new Paragraph!
`
} // set the Chapter at that index

b.set([C]{
[P]`
Good to see you
This is a new Paragraph!
`
}) // set the Chapter at that index


### String Types

[Glyph]` ... `
[Word]` ... `
[Sentence]` ... `
[Paragraph]` ... `
[Chapter]` ... `
[Book]` ... `

[G]` ... `
[W]` ... `
[S]` ... `
[P]` ... `
[C]` ... `
[B]` ... `