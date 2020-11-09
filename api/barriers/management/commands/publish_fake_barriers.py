import datetime
from datetime import timezone
import itertools
import random

from django.conf import settings
from django.core.management import BaseCommand

from api.barriers.models import PublicBarrier
from api.barriers.public_data import public_release_to_s3
from api.metadata.constants import BarrierStatus, PublicBarrierStatus
from api.metadata.utils import get_countries, get_sectors, get_trading_bloc_by_country_id


ALL_SECTORS_PROPORTION = 0.2

EU_PROPORTION = 0.1

ADJECTIVES = (
    "abrupt", "acidic", "adorable", "adventurous", "aggressive", "agitated", "alert", "aloof",
    "amiable", "amused", "annoyed", "antsy", "anxious", "appalling", "appetizing", "apprehensive",
    "arrogant", "ashamed", "astonishing", "attractive", "average", "batty", "beefy", "bewildered",
    "biting", "bitter", "bland", "blushing", "bored", "brave", "bright", "broad", "bulky", "burly",
    "charming", "cheeky", "cheerful", "chubby", "clean", "clear", "cloudy", "clueless", "clumsy",
    "colorful", "colossal", "combative", "comfortable", "condemned", "condescending", "confused",
    "contemplative", "convincing", "convoluted", "cooperative", "corny", "costly", "courageous",
    "crabby", "creepy", "crooked", "cruel", "cumbersome", "curved", "cynical", "dangerous",
    "dashing", "decayed", "deceitful", "deep", "defeated", "defiant", "delicious", "delightful",
    "depraved", "depressed", "despicable", "determined", "dilapidated", "diminutive", "disgusted",
    "distinct", "distraught", "distressed", "disturbed", "dizzy", "drab", "drained", "dull",
    "eager", "ecstatic", "elated", "elegant", "emaciated", "embarrassed", "enchanting",
    "encouraging", "energetic", "enormous", "enthusiastic", "envious", "exasperated", "excited",
    "exhilarated", "extensive", "exuberant", "fancy", "fantastic", "fierce", "filthy", "flat",
    "floppy", "fluttering", "foolish", "frantic", "fresh", "friendly", "frightened", "frothy",
    "frustrating", "funny", "fuzzy", "gaudy", "gentle", "ghastly", "giddy", "gigantic",
    "glamorous", "gleaming", "glorious", "gorgeous", "graceful", "greasy", "grieving", "gritty",
    "grotesque", "grubby", "grumpy", "handsome", "happy", "harebrained", "healthy", "helpful",
    "helpless", "high", "hollow", "homely", "horrific", "huge", "hungry", "hurt", "icy", "ideal",
    "immense", "impressionable", "intrigued", "irate", "irritable", "itchy", "jealous",
    "jittery", "jolly", "joyous", "juicy",
    "jumpy", "kind", "lackadaisical", "large", "lazy", "lethal", "little", "lively", "livid",
    "lonely", "loose", "lovely", "lucky", "ludicrous", "macho", "magnificent", "mammoth",
    "maniacal", "massive", "melancholy", "melted", "miniature", "minute", "mistaken", "misty",
    "moody", "mortified", "motionless", "muddy", "mysterious", "narrow", "nasty", "naughty",
    "nervous", "nonchalant", "nonsensical", "nutritious", "nutty", "obedient", "oblivious",
    "obnoxious", "odd", "old-fashioned", "outrageous", "panicky", "perfect", "perplexed",
    "petite", "petty", "plain", "pleasant", "poised", "pompous", "precious", "prickly", "proud",
    "pungent", "puny", "quaint", "quizzical", "ratty", "reassured", "relieved", "repulsive",
    "responsive", "ripe", "robust", "rotten", "rotund", "rough", "round", "salty", "sarcastic",
    "scant", "scary", "scattered", "scrawny", "selfish", "shaggy", "shaky", "shallow", "sharp",
    "shiny", "short", "silky", "silly", "skinny", "slimy", "slippery", "small", "smarmy",
    "smiling", "smoggy", "smooth", "smug", "soggy", "solid", "sore", "sour", "sparkling",
    "spicy", "splendid", "spotless", "square", "stale", "steady", "steep", "responsive",
    "sticky", "stormy", "stout", "straight", "strange", "strong", "stunning", "substantial",
    "successful", "succulent", "superficial", "superior", "swanky", "sweet", "tart", "tasty",
    "teeny", "tender", "tense", "terrible", "testy", "thankful", "thick", "thoughtful",
    "thoughtless", "tight", "timely", "tricky", "trite", "troubled", "uneven", "unsightly",
    "upset", "uptight", "vast", "vexed", "victorious", "virtuous", "vivacious", "vivid", "wacky",
    "weary", "whimsical", "whopping", "wicked", "witty", "wobbly", "wonderful", "worried",
    "yummy", "zany", "zealous", "zippy", "slithery", "red", "yellow", "blue", "green", "brown",
    "black", "white", "orange", "purple", "violet", "golden", "silver", "bronze",
)


NOUNS = [
    "Aardvarks", "Albatrosses", "Alligators", "Alpacas", "Angelfish", "Anteaters", "Antelopes",
    "Armadillos", "Badgers", "Barracudas", "Bats", "Beagles", "Bears", "Beavers", "Birds",
    "Brontosauruses", "Boa Constrictors", "Bulldogs", "Bumblebees", "Butterflies", "Camels", "Caribous",
    "Cassowaries", "Cats", "Catfish", "Caterpillars", "Centipedes", "Chameleons", "Cheetahs",
    "Chinchillas", "Chipmunks", "Cobras", "Coelacanths", "Condors", "Coral Snakes", "Cormorants", "Crabs",
    "Cranes", "Crocodiles", "Dalmatians", "Deer", "Dolphins", "Doves", "Dragonfish", "Dragonflies",
    "Ducks", "Eagles", "Eels", "Elephants", "Elks", "Falcons", "Ferrets", "Finchs", "Fireflies", "fish",
    "Flamingos", "Foxes", "Frogs", "Gazelles", "Geckos", "Gerbils", "Giraffes", "Gnus", "Goldfish",
    "Gooses", "Gorillas", "Grasshoppers", "Greyhounds", "Grouses", "Gulls", "Hamsters", "Hares", "Hawks",
    "Hatchetfish", "Hedgehogs", "Herons", "Herrings", "Hornets", "Horses", "Hummingbirds", "Ibexes",
    "Ibises", "Iguanas", "Jackals", "Jaguars", "Jellyfish", "Kangaroos", "Kestrels", "Kingfishers",
    "Koalas", "Koi", "Larks", "Lemurs", "Leopards", "Lions", "Lionfish", "Llamas", "Lobsters", "Lorises",
    "Magpies", "Mallards", "Mandrills", "Manta Rays", "Mantises", "Marlins", "Mastiffs", "Mollusks",
    "Mongooses", "Mooses", "Mouses", "Narwhals", "Nautiluses", "Newts", "Nightingales", "Octopuses",
    "Okapis", "Opossums", "Orcas", "Ospreys", "Ostrichs", "Otters", "Owls", "Pandas", "Panthers", "Parrots",
    "Partridges", "Pelicans", "Penguins", "Pheasants", "Pigeons", "Platypi", "Polar Bears",
    "Porcupines", "Porpoises", "Pythons", "Quails", "Rabbits", "Raccoons", "Rams", "Ravens", "Reindeer",
    "Rhinoceri", "Roadrunners", "Rooks", "Salamanders", "Salmons", "Sandpipers", "Scorpions",
    "Sea Cucumbers", "Sea Lions", "Sea Snakes", "Sea Turtles", "Seahorses", "Seals", "Sharks", "Sheep",
    "Snowy Owls", "Songbirds", "Sparrows", "Spiders", "Squids", "Squirrels", "Starfish", "Starlings",
    "Stegosauruses", "Stingrays", "Storks", "Swans", "Tapirs", "Tigers", "Toucans", "Triceratops",
    "Turtles", "Vampire Bats", "Velociraptors", "Wallabies", "Walruses", "Wolves", "Wolverines", "Wombats",
    "Wrasses", "Wrens", "Yaks", "Zebras", "apples", "backs", "balls", "bears", "beds", "bells",
    "birds", "birthdays", "boats", "boxs", "boys", "breads", "cakes", "cars", "cats", "chairs",
    "chickens", "coats", "corn", "cows", "days", "dogs", "dolls", "doors", "ducks", "eggs",
    "eyes", "farms", "farmers", "feets", "fires", "fish", "floors", "flowers", "games",
    "gardens", "grasss", "grounds", "hands", "heads", "hills", "homes", "horses", "houses",
    "kitties", "legs", "letters", "milks", "money", "mornings", "names", "nests",
    "nights", "papers", "parties", "pictures", "pigs", "rabbits", "rain", "rings", "robins", "schools",
    "seeds", "shoes", "snow", "songs", "sticks", "streets", "stars", "tables", "things", "times",
    "tops", "toys", "trees", "watches", "water", "winds", "windows", "woods",
    "Jelly Babies", "Jelly Beans", "Wizards", "Beer", "Halloumi",
]


class Randomiser:
    _sectors = None
    _countries = None

    @property
    def countries(self):
        if self._countries is None:
            self._countries = [
                country["id"]
                for country in get_countries()
                if country["disabled_on"] is None
                and country.get("id")
            ]
        return self._countries

    @property
    def sectors(self):
        if self._sectors is None:
            self._sectors = [
                sector["id"] for sector in get_sectors()
                if sector["level"] == 0
                and sector["disabled_on"] is None
                and sector.get("id")
            ]
        return self._sectors

    def get_title(self):
        return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}".title()

    def get_sectors(self):
        quantity = random.choices(
            population=[0, 1, 2, 3],
            weights=[0.1, 0.6, 0.2, 0.1],
        )[0]
        return random.choices(self.sectors, k=quantity)

    def get_country(self):
        return random.choice(self.countries)

    def get_status(self):
        statuses = (
            BarrierStatus.OPEN_PENDING,
            BarrierStatus.OPEN_IN_PROGRESS,
            BarrierStatus.RESOLVED_IN_PART,
            BarrierStatus.RESOLVED_IN_FULL,
        )
        return random.choice(statuses)


def create_fake_public_barriers(quantity):
    earliest_publish_date = datetime.datetime(2020, 8, 1, tzinfo=timezone.utc)
    id_generator = itertools.count(1).__next__
    randomiser = Randomiser()

    for i in range(quantity):
        if random.random() > ALL_SECTORS_PROPORTION:
            sectors = randomiser.get_sectors()
            all_sectors = False
        else:
            sectors = []
            all_sectors = True

        if random.random() > EU_PROPORTION:
            country = randomiser.get_country()
            trading_bloc = ""
            caused_by_trading_bloc = False
            country_trading_bloc = get_trading_bloc_by_country_id(country)
            if country_trading_bloc and random.random() > 0.8:
                caused_by_trading_bloc = True
        else:
            country = None
            trading_bloc = "TB00016"
            caused_by_trading_bloc = False

        status = randomiser.get_status()

        if status in (BarrierStatus.RESOLVED_IN_FULL, BarrierStatus.RESOLVED_IN_PART):
            status_date = datetime.date(
                random.randint(2014, 2020),
                random.randint(1, 12),
                1,
            )
        else:
            status_date = None

        published_date = earliest_publish_date + datetime.timedelta(days=random.randint(1, 100))

        yield PublicBarrier(
            id=id_generator(),
            _title=randomiser.get_title(),
            _summary="Lorem ipsum dolor",
            status=status,
            status_date=status_date,
            country=country,
            caused_by_trading_bloc=caused_by_trading_bloc,
            trading_bloc=trading_bloc,
            sectors=sectors,
            all_sectors=all_sectors,
            _public_view_status=PublicBarrierStatus.PUBLISHED,
            first_published_on=published_date,
            last_published_on=published_date,
        )


class Command(BaseCommand):
    help = "Publish fake barriers"

    def add_arguments(self, parser):
        parser.add_argument("quantity", type=int, help="Number of barriers to publish")

    def handle(self, *args, **options):
        if settings.DJANGO_ENV in ["local", "dev"]:
            quantity = options["quantity"]
            self.stdout.write(f"Publishing {quantity} fake barriers...")
            public_barriers = create_fake_public_barriers(quantity)
            public_release_to_s3(public_barriers)
        else:
            self.stdout.write(f"Publishing fake barriers is disabled on {settings.DJANGO_ENV}")
