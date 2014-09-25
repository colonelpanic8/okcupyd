from .errors import InvalidInputError


sep_replacements = ('\\', '/', '.', '-', ' ', '$', ',', '(', ')')


seeking = {
    'girls who like guys': '34',
    'guys who like girls': '17',
    'girls who like girls': '40',
    'guys who like guys': '20',
    'both who like bi guys': '54',
    'both who like bi girls': '57',
    'straight girls only': '2',
    'straight guys only': '1',
    'gay girls only': '8',
    'gay guys only': '4',
    'bi girls only': '32',
    'bi guys only': '16',
    'bi guys and girls': '48',
    'everybody': '63',
    '': '63'
}


# Wtf, OKCupid?
has_kids = {
    "has a kid": {"addition": 33686018, "power": 1},
    "has kids": {"addition": 67372036, "power": 2},
    "doesn't have kids": {"addition": 1077952576, "power": 6},
}


wants_kids = {
    "might want kids": {"addition": 18176, "power": 8},
    "wants kids": {"addition": 4653056, "power": 16},
    "doesn't want kids": {"addition": 1191182384, "power": 24},
}


language_map = {
    'English': '74',
    'Afrikaans': '2',
    'Albanian': '3',
    'Ancient Greek': '27',
    'Arabic': '4',
    'Armenian': '76',
    'Basque': '5',
    'Belarusan': '6',
    'Bengali': '7',
    'Breton': '8',
    'Bulgarian': '9',
    'C++': '71',
    'Catalan': '10',
    'Cebuano': '11',
    'Chechen': '12',
    'Chinese': '13',
    'Croatian': '14',
    'Czech': '15',
    'Danish': '16',
    'Dutch': '17',
    'Esperanto': '18',
    'Estonian': '19',
    'Farsi': '20',
    'Finnish': '21',
    'French': '22',
    'Frisian': '23',
    'Georgian': '24',
    'German': '25',
    'Greek': '26',
    'Gujarati': '77',
    'Hawaiian': '28',
    'Hebrew': '29',
    'Hindi': '75',
    'Hungarian': '30',
    'Icelandic': '31',
    'Ilongo': '32',
    'Indonesian': '33',
    'Irish': '34',
    'Italian': '35',
    'Japanese': '36',
    'Khmer': '37',
    'Korean': '38',
    'LISP': '72',
    'Latin': '39',
    'Latvian': '40',
    'Lithuanian': '41',
    'Malay': '42',
    'Maori': '43',
    'Mongolian': '44',
    'Norwegian': '45',
    'Occitan': '46',
    'Other': '73',
    'Persian': '47',
    'Polish': '48',
    'Portuguese': '49',
    'Romanian': '50',
    'Rotuman': '51',
    'Russian': '52',
    'Sanskrit': '53',
    'Sardinian': '54',
    'Serbian': '55',
    'Sign Language': '1',
    'Slovak': '56',
    'Slovenian': '57',
    'Spanish': '58',
    'Swahili': '59',
    'Swedish': '60',
    'Tagalog': '61',
    'Tamil': '62',
    'Thai': '63',
    'Tibetan': '64',
    'Turkish': '65',
    'Ukrainian': '66',
    'Urdu': '67',
    'Vietnamese': '68',
    'Welsh': '69',
    'Yiddish': '70',
}


binary_lists = {
    'smokes': ['11', 'yes', 'sometimes', 'when drinking', 'trying to quit', 'no'],
    'drinks': ['12', 'very often', 'often', 'socially', 'rarely', 'desperately',
               'not at all'],
    'drugs': ['13', 'never', 'sometimes', 'often'],
    'education': ['19', 'high school', 'two-year college', 'college/university',
                  'masters program', 'law school', 'medical school',
                  'ph.d program'],
    'job': ['15', 'student', 'art / music / writing', 'banking / finance',
            'administration', 'technology', 'construction', 'education',
            'entertainment / media', 'management', 'hospitality', 'law',
            'medicine', 'military', 'politics / government',
            'sales / marketing', 'science / engineering', 'transporation',
            'retired'],
    'income': ['14', 'less than $20,000', '$20,000-$30,000', '$30,000-$40,000',
               '$40,000-$50,000', '$50,000-$60,000', '$60,000-$70,000',
               '$70,000-$80,000', '$80,000-$100,000', '$100,000-$150,000',
               '$150,000-$250,000', '$250,000-$500,000', '$500,000-$1,000,000',
               'More than $1,000,000'],
    'religion': ['8', 'agnostic', 'atheist', 'christian', 'jewish', 'catholic',
                 'muslim', 'hindu', 'buddhist', 'other'],
    'monogamy': ['73', 'monogamous', 'non-monogamous'],
    'diet': ['54', 'vegetarian', 'vegan', 'kosher', 'halal'],
    'sign': ['21', 'acquarius', 'pisces', 'aries', 'taurus', 'gemini',
             'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius',
             'capricorn'],
    'ethnicity': ['9', 'asian', 'middle eastern', 'black', 'native american',
                  'indian', 'pacific islander', 'hispanic/latin', 'white',
                  'human (other)']
    }


dogs = ['owns dogs', 'likes dogs', 'dislikes dogs']
cats = ['owns cats', 'likes cats', 'dislikes cats']


def get_height_query(height_min, height_max):
    '''Convert from inches to millimeters/10'''
    min_int = 0
    max_int = 99999
    if height_min is not None:
        min_int = int(height_min) * 254
    if height_max is not None:
        max_int = int(height_max) * 254
    return '10,{0},{1}'.format(str(min_int), str(max_int))


def get_options_query(type, inputs):
    for char in sep_replacements:
        inputs = [input.replace(char, '') for input in inputs]
    inputs = [input.lower() for input in inputs]
    if type in binary_lists:
        start = 1
        option_list = binary_lists[type]
    if type == 'drugs':
        start = 0
    if type == 'diet':
        start = 2
    int_to_return = 0
    for power, option in enumerate(option_list[1:], start=start):
        for char in sep_replacements:
            option = option.replace(char, '')
        if option in inputs:
            int_to_return += 2**power
    return '{0},{1}'.format(option_list[0], int_to_return)


def get_pet_queries(pets):
    for char in sep_replacements:
        pets = [pet.replace(char, '') for pet in pets]
    pets = [pet.lower() for pet in pets]
    dog_int = 0
    cat_int = 0
    for power, option in enumerate(dogs, start=1):
        for char in sep_replacements:
            option = option.replace(char, '')
        if option in pets:
            dog_int += 2**power
    for power, option in enumerate(cats, start=1):
        for char in sep_replacements:
            option = option.replace(char, '')
        if option in pets:
            cat_int += 2**power
    dog_query = '16,{0}'.format(dog_int)
    cat_query = '17,{0}'.format(cat_int)
    return dog_query, cat_query


def get_kids_query(kids):
    kids = [kid.lower() for kid in kids]
    kid_int = 0
    include_has = False
    include_wants = False
    for option in kids:
        if option in has_kids:
            include_has = True
        elif option in wants_kids:
            include_wants = True
    if include_has and not include_wants:
        for option in kids:
            if option in has_kids:
                kid_int += has_kids[option]['addition']
    elif include_wants and not include_has:
        for option in kids:
            if option in wants_kids:
                kid_int += wants_kids[option]['addition']
    elif include_wants and include_has:
        for has_option in kids:
            if has_option in has_kids:
                for wants_option in kids:
                    if wants_option in wants_kids:
                        kid_int += 2**(has_kids[has_option]['power'] + wants_kids[wants_option]['power'])
    return '18,{0}'.format(kid_int)


def get_language_query(language):
    return '22,{0}'.format(language_map[language.title()])


def get_join_date_query(date):
    date_int = 0
    if isinstance(date, str) and not date.isdigit():
        if date.lower() in ('hour', 'last hour'):
            date_int = 3600
        elif date.lower() in ('day', 'last day'):
            date_int = 86400
        elif date.lower() in ('week', 'last week'):
            date_int = 604800
        elif date.lower() in ('month', 'last month'):
            date_int = 2678400
        elif date.lower() in ('year', 'last year'):
            date_int = 31536000 
        elif date.lower() in ('decade', 'last decade'):
            date_int = 315360000
        else:
            raise InvalidInputError('Could not parse date string')
    else:
        date_int = date
    return '6,{0}'.format(date_int)
