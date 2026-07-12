from pathlib import Path
import json

ROOT = Path(__file__).parents[1] / "benchmarks"
facts = {
"history": [("George Washington","first U.S. president"),("Abraham Lincoln","president who issued the Emancipation Proclamation"),("Thomas Jefferson","principal Declaration of Independence author"),("James Madison","principal Constitution author"),("1776","year the Declaration was adopted"),("1861","year the U.S. Civil War began"),("1945","year World War II ended"),("1989","year the Berlin Wall fell"),("Martin Luther King Jr.","civil-rights leader who gave the I Have a Dream speech"),("Mahatma Gandhi","Indian independence leader known for nonviolence"),("Winston Churchill","British prime minister during most of World War II"),("Joseph Stalin","Soviet leader during World War II"),("Treaty of Versailles","treaty ending World War I"),("Magna Carta","1215 document limiting English royal power"),("Black Death","14th-century European pandemic"),("Silk Road","trade route linking China and the Mediterranean"),("Pompeii","Roman city buried by Vesuvius"),("Inca","civilization that built Machu Picchu"),("NATO","1949 collective-defense alliance"),("Brown v. Board of Education","case ending legal school segregation"),("Waterloo","Napoleon’s final defeat"),("Mayflower","ship carrying Pilgrims in 1620"),("Jamestown","first permanent English settlement"),("Neil Armstrong","first person to walk on the Moon"),("Alexander Fleming","scientist who discovered penicillin")],
"science": [("Au","chemical symbol for gold"),("Na","chemical symbol for sodium"),("6","atomic number of carbon"),("Carbon dioxide","gas plants absorb for photosynthesis"),("Nitrogen","most abundant atmospheric gas"),("7","pH of a neutral solution"),("Mercury","planet closest to the Sun"),("Jupiter","largest planet"),("Mars","Red Planet"),("Saturn","planet famous for rings"),("Gravity","force keeping planets in orbit"),("Milky Way","galaxy containing our solar system"),("Heart","organ that pumps blood"),("Skin","largest human organ"),("DNA","molecule carrying genetic instructions"),("Cell","basic unit of life"),("Photosynthesis","process plants use to make food"),("Nucleus","cell structure that contains DNA"),("Newton","SI unit of force"),("Ampere","SI unit of electric current"),("Refraction","bending of light"),("Evaporation","liquid-to-gas change"),("Cumulonimbus","cloud type associated with thunderstorms"),("Magma","molten rock below Earth’s surface"),("Neutron","electrically neutral atomic particle")],
"geography": [("Pacific Ocean","largest ocean"),("Asia","largest continent"),("Amazon River","longest river in South America"),("Mount Everest","highest mountain above sea level"),("Sahara Desert","largest hot desert"),("Tokyo","capital of Japan"),("Ottawa","capital of Canada"),("Canberra","capital of Australia"),("Brasília","capital of Brazil"),("Cairo","capital of Egypt"),("Russia","largest country by area"),("Italy","boot-shaped country"),("Egypt","country containing the Great Pyramids"),("Peru","country containing Machu Picchu"),("River Thames","river through London"),("Seine","river through Paris"),("Mediterranean Sea","sea between Europe and Africa"),("Bering Strait","waterway separating Alaska and Russia"),("Mariana Trench","deepest ocean trench"),("Victoria Falls","waterfall on the Zambia-Zimbabwe border"),("Antarctica","continent entirely in the Southern Hemisphere"),("Equator","line dividing the Northern and Southern Hemispheres"),("Prime Meridian","line at zero degrees longitude"),("Alaska","largest U.S. state by area"),("Ural Mountains","conventional Europe-Asia boundary range")],
"civics": [("Constitution","supreme law of the United States"),("3","number of federal government branches"),("Legislative branch","branch that makes federal laws"),("Executive branch","branch that enforces federal laws"),("Judicial branch","branch that interprets laws"),("President","head of the executive branch"),("2","senators per state"),("435","voting House members"),("6 years","Senate term length"),("2 years","House term length"),("4 years","presidential term length"),("35","minimum presidential age"),("30","minimum Senate age"),("Supreme Court","highest U.S. court"),("9","Supreme Court justices"),("First Amendment","amendment protecting free speech"),("Second Amendment","amendment protecting the right to bear arms"),("Thirteenth Amendment","amendment abolishing slavery"),("Nineteenth Amendment","amendment giving women the vote"),("Twenty-sixth Amendment","amendment lowering voting age to 18"),("Bill of Rights","name for the first ten amendments"),("Veto","presidential rejection of a bill"),("Federalism","division of national and state power"),("Census","population count"),("Naturalization","process of becoming a U.S. citizen")]
}
for category, entries in facts.items():
    target = ROOT / category; target.mkdir(parents=True, exist_ok=True); rows=[]
    for n, (answer, clue) in enumerate(entries, 1):
        for prompt in (f"What is the {clue}?", f"Name the {clue}."):
            i=len(rows)+1; rows.append({"id":f"{category}-{i:03}","title":f"{category.title()} fact {i}","category":category.title(),"difficulty":"Core","prompt":prompt,"answer":[answer]})
    assert len(rows)==50
    (target/"core.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n",encoding="utf-8")
(ROOT/"manifest.json").write_text(json.dumps({"format":"benchmark-atlas-jsonl/v1","packs":[{"category":k.title(),"path":f"{k}/core.jsonl","count":50} for k in facts]},indent=2)+"\n",encoding="utf-8")

# Additional unique-question packs. These use pack-level authoritative references
# in the manifest while retaining the v1 row schema consumed by the client.
extra = {
"mathematics": """
What is 12 multiplied by 12?|144
What is the square root of 169?|13
What is 15 percent of 200?|30
What is 7 cubed?|343
What is the value of pi rounded to two decimal places?|3.14
What is the sum of the interior angles of a triangle in degrees?|180
How many degrees are in a right angle?|90
What is the perimeter of a square with side length 6?|24
What is the area of a rectangle 8 units long and 5 units wide?|40
What is the area of a triangle with base 10 and height 6?|30
What is the circumference formula for a circle of radius r?|2πr
What is the area formula for a circle of radius r?|πr²
What is the next prime number after 19?|23
What is the greatest common divisor of 24 and 36?|12
What is the least common multiple of 6 and 8?|24
What fraction is equivalent to 0.75 in lowest terms?|3/4
What decimal is equivalent to one eighth?|0.125
What is 2 to the tenth power?|1024
Solve for x: x plus 9 equals 17.|8
Solve for x: 3x equals 27.|9
What is the slope of the line y equals 2x plus 5?|2
What is the y-intercept of y equals 3x minus 4?|-4
What is the absolute value of minus 12?|12
What is the additive inverse of 7?|-7
What is the reciprocal of 5?|1/5
How many sides does a hexagon have?|6
How many sides does a dodecagon have?|12
What is a polygon with eight sides called?|octagon
What is the longest side of a right triangle called?|hypotenuse
What theorem states that a squared plus b squared equals c squared for a right triangle?|Pythagorean theorem
What is the median of 2, 4, 7, 9, and 12?|7
What is the mean of 4, 6, 8, and 10?|7
What is the mode of 1, 2, 2, 3, and 4?|2
What is the probability of rolling a 6 on a fair six-sided die?|1/6
What is the probability of heads on a fair coin toss?|1/2
How many meters are in one kilometer?|1000
How many centimeters are in one meter?|100
What is 3.5 plus 2.75?|6.25
What is 10 factorial?|3628800
What is the derivative of x squared with respect to x?|2x
What is the derivative of sin x with respect to x?|cos x
What is the indefinite integral of 1 with respect to x?|x + C
What is log base 10 of 1000?|3
What is the binary representation of decimal 10?|1010
What Roman numeral represents 50?|L
What is the sum of the first five positive integers?|15
Is zero an even or odd integer?|even
What is the only even prime number?|2
What is the golden ratio commonly denoted by?|phi
What branch of mathematics studies rates of change and accumulation?|calculus
""",
"computing": """
What does CPU stand for?|Central Processing Unit
What does RAM stand for?|Random Access Memory
What does URL stand for?|Uniform Resource Locator
What does HTTP stand for?|Hypertext Transfer Protocol
What does HTTPS add to HTTP?|encryption
What does DNS translate domain names into?|IP addresses
What does HTML stand for?|Hypertext Markup Language
What language is primarily used to style web pages?|CSS
What language commonly adds interactivity to web pages?|JavaScript
What binary digit values are possible?|0 and 1
How many bits are in a byte?|8
What is the hexadecimal value of decimal 15?|F
What data structure uses last in, first out ordering?|stack
What data structure uses first in, first out ordering?|queue
What search algorithm repeatedly halves a sorted search interval?|binary search
What is the worst-case time complexity of linear search?|O(n)
What is the typical time complexity of lookup in a hash table?|O(1)
What programming construct repeats a block of code?|loop
What programming construct chooses between paths based on a condition?|conditional
What is a named reusable block of code commonly called?|function
What does API stand for?|Application Programming Interface
What does JSON stand for?|JavaScript Object Notation
What character begins a JSON object?|{
What distributed version-control system was created by Linus Torvalds?|Git
What Git command copies a remote repository locally?|git clone
What Git command records staged changes?|git commit
What SQL command retrieves rows from a database?|SELECT
What database structure uniquely identifies a table row?|primary key
What database operation combines rows from related tables?|join
What does OS stand for in computing?|operating system
Which operating-system component manages hardware and system resources?|kernel
What protocol securely connects to a remote command shell?|SSH
What does VPN stand for?|Virtual Private Network
What security property ensures data was not altered?|integrity
What process converts plaintext into unreadable ciphertext?|encryption
What type of malware demands payment to restore access?|ransomware
What is a secret used with a username to authenticate called?|password
What extra security step beyond a password is abbreviated MFA?|multi-factor authentication
What cloud model provides virtual machines and networking resources?|Infrastructure as a Service
What does SaaS stand for?|Software as a Service
What container platform uses images and Dockerfiles?|Docker
What orchestration system is commonly used to manage containers at scale?|Kubernetes
What is an isolated copy of a running program called?|process
What smaller execution unit within a process is called?|thread
What bug occurs when concurrent operations access shared data unpredictably?|race condition
What technique stores results for faster reuse?|caching
What response status code means HTTP Not Found?|404
What HTTP method is conventionally used to retrieve a resource?|GET
What HTTP method is conventionally used to create a resource?|POST
What design style commonly exposes resources through HTTP endpoints?|REST
""",
"literature": """
Who wrote Pride and Prejudice?|Jane Austen
Who wrote 1984?|George Orwell
Who wrote The Great Gatsby?|F. Scott Fitzgerald
Who wrote Moby-Dick?|Herman Melville
Who wrote The Odyssey?|Homer
Who wrote Don Quixote?|Miguel de Cervantes
Who wrote One Hundred Years of Solitude?|Gabriel García Márquez
Who wrote Beloved?|Toni Morrison
Who wrote The Divine Comedy?|Dante Alighieri
Who wrote The Canterbury Tales?|Geoffrey Chaucer
Who wrote Crime and Punishment?|Fyodor Dostoevsky
Who wrote War and Peace?|Leo Tolstoy
Who wrote Frankenstein?|Mary Shelley
Who wrote Jane Eyre?|Charlotte Brontë
Who wrote Wuthering Heights?|Emily Brontë
Who wrote The Catcher in the Rye?|J. D. Salinger
Who wrote The Old Man and the Sea?|Ernest Hemingway
Who wrote Things Fall Apart?|Chinua Achebe
Who wrote The Handmaid's Tale?|Margaret Atwood
Who wrote Invisible Man?|Ralph Ellison
Who wrote The Color Purple?|Alice Walker
Who wrote The Stranger?|Albert Camus
Who wrote The Metamorphosis?|Franz Kafka
Who wrote The Picture of Dorian Gray?|Oscar Wilde
Who wrote Gulliver's Travels?|Jonathan Swift
Who wrote The Scarlet Letter?|Nathaniel Hawthorne
Who wrote The Sun Also Rises?|Ernest Hemingway
Who wrote Mrs Dalloway?|Virginia Woolf
Who wrote Middlemarch?|George Eliot
Who wrote The Brothers Karamazov?|Fyodor Dostoevsky
Who wrote The Iliad?|Homer
Who wrote The Aeneid?|Virgil
Who wrote Paradise Lost?|John Milton
Who wrote Leaves of Grass?|Walt Whitman
Who wrote The Waste Land?|T. S. Eliot
Who wrote I Know Why the Caged Bird Sings?|Maya Angelou
Who wrote The Hobbit?|J. R. R. Tolkien
Who wrote The Lion, the Witch and the Wardrobe?|C. S. Lewis
Who wrote The Little Prince?|Antoine de Saint-Exupéry
Who wrote The Tale of Genji?|Murasaki Shikibu
What literary device compares two things using like or as?|simile
What literary device directly compares two unlike things without like or as?|metaphor
What term means giving human traits to nonhuman things?|personification
What is the central character of a story called?|protagonist
What character or force opposes the protagonist?|antagonist
What is a fourteen-line poem commonly called?|sonnet
What Japanese poetic form traditionally has three lines and seventeen syllables?|haiku
What is a story's time and place called?|setting
What is the sequence of events in a story called?|plot
What narrative perspective uses the pronoun I?|first person
"""
}

references = {
    "mathematics": ["https://mathworld.wolfram.com/", "https://www.nist.gov/pml/owm/si-units-length"],
    "computing": ["https://developer.mozilla.org/en-US/docs/Web", "https://git-scm.com/docs", "https://www.rfc-editor.org/"],
    "literature": ["https://www.loc.gov/books/", "https://www.britannica.com/art/literature"],
}
for category, raw in extra.items():
    pairs = [line.split("|", 1) for line in raw.strip().splitlines()]
    assert len(pairs) == 50, (category, len(pairs))
    rows = []
    for i, (prompt, answer) in enumerate(pairs, 1):
        rows.append({"id": f"{category}-{i:03}", "title": f"{category.title()} question {i}",
                     "category": category.title(), "difficulty": "Core",
                     "prompt": prompt, "answer": [answer]})
    target = ROOT / category
    target.mkdir(parents=True, exist_ok=True)
    (target / "core.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")

manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
for category in extra:
    manifest["packs"].append({"category": category.title(), "path": f"{category}/core.jsonl",
                              "count": 50, "references": references[category]})
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
