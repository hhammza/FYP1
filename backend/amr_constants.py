"""
Antibiotic names and label maps, in one place.

Every part of the project reads these from here: the cleaning in
experiments/lib/data_prep.py, the trainer (train_models.py), the predictors
(ml_models/), the API and, through the generated frontend/antibiotic_names.json,
the web pages. Standard library only, so each of them can load it.

After editing, run `python backend/amr_constants.py` to regenerate the
frontend copy; backend/tests/test_amr_constants.py fails until you do. A
change that alters the cleaned table also needs CLEAN_VERSION bumped in
data_prep.py.
"""
import json
import os

# Drug class per canonical antibiotic name. Anything missing is 'other'.
DRUG_CLASS_MAP = {
    'ampicillin': 'beta_lactam', 'amoxicillin': 'beta_lactam',
    'amoxicillin/clavulanic acid': 'beta_lactam', 'piperacillin': 'beta_lactam',
    'piperacillin/tazobactam': 'beta_lactam', 'oxacillin': 'beta_lactam',
    'ampicillin/sulbactam': 'beta_lactam', 'penicillin': 'beta_lactam',
    'methicillin': 'beta_lactam', 'carbenicillin': 'beta_lactam',
    'cefazolin': 'beta_lactam', 'cefoxitin': 'beta_lactam', 'cefotaxime': 'beta_lactam',
    'ceftazidime': 'beta_lactam', 'ceftriaxone': 'beta_lactam', 'cefepime': 'beta_lactam',
    'cefuroxime': 'beta_lactam', 'cephalothin': 'beta_lactam', 'cefalothin': 'beta_lactam',
    'ceftazidime/avibactam': 'beta_lactam', 'ceftolozane/tazobactam': 'beta_lactam',
    'ceftiofur': 'beta_lactam', 'cefpodoxime': 'beta_lactam',
    'imipenem': 'carbapenem', 'meropenem': 'carbapenem', 'ertapenem': 'carbapenem',
    'doripenem': 'carbapenem', 'aztreonam': 'monobactam',
    'ciprofloxacin': 'fluoroquinolone', 'levofloxacin': 'fluoroquinolone',
    'norfloxacin': 'fluoroquinolone', 'nalidixic acid': 'fluoroquinolone',
    'ofloxacin': 'fluoroquinolone', 'moxifloxacin': 'fluoroquinolone',
    'pefloxacin': 'fluoroquinolone', 'trovafloxacin': 'fluoroquinolone',
    'gentamicin': 'aminoglycoside', 'tobramycin': 'aminoglycoside',
    'amikacin': 'aminoglycoside', 'streptomycin': 'aminoglycoside',
    'neomycin': 'aminoglycoside', 'kanamycin': 'aminoglycoside',
    'spectinomycin': 'aminoglycoside', 'capreomycin': 'aminoglycoside',
    'tetracycline': 'tetracycline', 'doxycycline': 'tetracycline',
    'minocycline': 'tetracycline', 'tigecycline': 'tetracycline',
    'sulfamethoxazole': 'sulfonamide', 'trimethoprim': 'sulfonamide',
    'trimethoprim/sulfamethoxazole': 'sulfonamide', 'sulfisoxazole': 'sulfonamide',
    'chloramphenicol': 'phenicol',
    'azithromycin': 'macrolide', 'erythromycin': 'macrolide',
    'telithromycin': 'macrolide', 'clarithromycin': 'macrolide',
    'colistin': 'polymyxin', 'polymyxin b': 'polymyxin',
    'vancomycin': 'glycopeptide', 'teicoplanin': 'glycopeptide',
    'clindamycin': 'lincosamide', 'nitrofurantoin': 'nitrofuran',
    'rifampicin': 'rifamycin', 'rifampin': 'rifamycin', 'rifabutin': 'rifamycin',
    'linezolid': 'oxazolidinone', 'daptomycin': 'lipopeptide',
    'fusidic acid': 'fusidane', 'quinupristin/dalfopristin': 'streptogramin',
    'pristinamycin': 'streptogramin', 'cephalexin': 'beta_lactam',
    'cefpodoxime/clavulanic acid': 'beta_lactam', 'ticarcillin/clavulanic acid': 'beta_lactam',
    'isoniazid': 'antitubercular', 'ethambutol': 'antitubercular',
    'pyrazinamide': 'antitubercular', 'ethionamide': 'antitubercular',
    'prothionamide': 'antitubercular', 'cycloserine': 'antitubercular',
    'para-aminosalicylic acid': 'antitubercular', 'clofazimine': 'antitubercular',
    'delamanid': 'antitubercular', 'bedaquiline': 'antitubercular',
    # v4: drugs in the export (or the UI list) that fell into 'other'.
    # Only azidothymidine (an antiviral) is left there on purpose.
    'cefixime': 'beta_lactam', 'cefpirome': 'beta_lactam', 'cefoperazone': 'beta_lactam',
    'cefotetan': 'beta_lactam', 'cefiderocol': 'beta_lactam', 'ceftaroline': 'beta_lactam',
    'cefovecin': 'beta_lactam', 'cefamandole': 'beta_lactam', 'cefaclor': 'beta_lactam',
    'cefmetazole': 'beta_lactam', 'ceftizoxime': 'beta_lactam', 'cefdinir': 'beta_lactam',
    'cefozopran': 'beta_lactam', 'ceftobiprole': 'beta_lactam', 'ceftibuten': 'beta_lactam',
    'ceftriaxone/cefpodoxime': 'beta_lactam', 'cefotaxime/clavulanic acid': 'beta_lactam',
    'ceftazidime/clavulanic acid': 'beta_lactam', 'cefoperazone/sulbactam': 'beta_lactam',
    'cefepime/taniborbactam': 'beta_lactam', 'temocillin': 'beta_lactam',
    'ticarcillin': 'beta_lactam', 'mecillinam': 'beta_lactam', 'sulbactam': 'beta_lactam',
    'imipenem/relebactam': 'carbapenem',
    'netilmicin': 'aminoglycoside', 'plazomicin': 'aminoglycoside', 'apramycin': 'aminoglycoside',
    'gatifloxacin': 'fluoroquinolone', 'enrofloxacin': 'fluoroquinolone',
    'danofloxacin': 'fluoroquinolone', 'sparfloxacin': 'fluoroquinolone',
    'pradofloxacin': 'fluoroquinolone', 'delafloxacin': 'fluoroquinolone',
    'chlortetracycline': 'tetracycline', 'oxytetracycline': 'tetracycline',
    'eravacycline': 'tetracycline', 'omadacycline': 'tetracycline',
    'sulfathiazole': 'sulfonamide', 'sulfamethazine': 'sulfonamide',
    'trimethoprim/sulfobactam': 'sulfonamide',
    'tylosin': 'macrolide', 'tulathromycin': 'macrolide', 'spiramycin': 'macrolide',
    'florfenicol': 'phenicol', 'lincomycin': 'lincosamide', 'virginiamycin': 'streptogramin',
    'furazolidone': 'nitrofuran', 'metronidazole': 'nitroimidazole',
    'fosfomycin': 'phosphonic_acid', 'mupirocin': 'pseudomonic_acid',
    'zoliflodacin': 'spiropyrimidinetrione', 'avilamycin': 'orthosomycin',
    'nicotinamide': 'antitubercular',   # all 229 rows are Mycobacterium
}

# Spelling variants, typos and non-drugs found in the raw Antibiotic column.
# Left-hand side is what appears in the export; right-hand side is canonical.
# None means "drop these rows", a drug class is not a drug.
ANTIBIOTIC_ALIASES = {
    'ampicillin-sulbactam': 'ampicillin/sulbactam',
    'ampicillin_clavulanic_acid': 'amoxicillin/clavulanic acid',
    'amoxicillin-clavulanic acid': 'amoxicillin/clavulanic acid',
    'piperacillin-tazobactam': 'piperacillin/tazobactam',
    'trimethoprim-sulfamethoxazole': 'trimethoprim/sulfamethoxazole',
    'sulfamethoxazole/trimethoprim': 'trimethoprim/sulfamethoxazole',
    'co_trimoxazole': 'trimethoprim/sulfamethoxazole',
    'co-trimoxazole': 'trimethoprim/sulfamethoxazole',
    'geamycin': 'gentamicin',
    'trimotheprim': 'trimethoprim',
    'cefalothin': 'cephalothin',
    'rifampin': 'rifampicin',
    # Separator variants of combination drugs
    'tazobactam_piperacillin': 'piperacillin/tazobactam',
    'ceftazidime_avibactam': 'ceftazidime/avibactam',
    'ceftolozane_tazobactam': 'ceftolozane/tazobactam',
    'ticarcillin_clavulanate': 'ticarcillin/clavulanic acid',
    'cefpodoxime_clavulanic_acid': 'cefpodoxime/clavulanic acid',
    'trimethoprim_sulfobactam': 'trimethoprim/sulfobactam',
    'para_aminosalicylic_acid': 'para-aminosalicylic acid',
    'cefepime_taniborbactam': 'cefepime/taniborbactam',
    'amoxicillin_clavulanat': 'amoxicillin/clavulanic acid',
    'polymyxin_b': 'polymyxin b',
    'ceftazidime-avibactam': 'ceftazidime/avibactam',
    'ceftolozane-tazobactam': 'ceftolozane/tazobactam',
    'imipenem-relebactam': 'imipenem/relebactam',
    # Typos and a broken character encoding
    'amipicillin_sulbactam': 'ampicillin/sulbactam',
    'tgecycline': 'tigecycline',
    'cefuroxim\u00e2': 'cefuroxime',
    'pristimycin': 'pristinamycin',
    'cefotaxime/clavulanic acid\u00e2': 'cefotaxime/clavulanic acid',
    # Other-language spellings, found by Suleman in BVBRC_genome_amr.csv
    'tigecyklin': 'tigecycline',
    'tetracyklin': 'tetracycline',
    'cefpirom': 'cefpirome',
    # Shigella panel; never on the same genome as nitrofurantoin
    'strofurantoin': 'nitrofurantoin',
    # Alternative names for the same drug
    'cefuroxime_sodium': 'cefuroxime',
    'cefalotin': 'cephalothin',
    'cefalexin': 'cephalexin',
    'synercid': 'quinupristin/dalfopristin',
    'phosphomycin': 'fosfomycin',
    'benzylpenicillin': 'penicillin',
    # Not a single drug: drug classes, a phenotype, and a lost drug name
    # ('instrument' is 593 C. difficile lab rows with the drug name missing)
    'carbapenem': None,
    'beta-lactam': None,
    'cephalosporin': None,
    'fluoroquinolones': None,
    'aminogycosides': None,
    'macrolides': None,
    'sulfonamides': None,
    'sulfa': None,
    'extended spectrum beta lactamase': None,
    'instrument': None,
}

# Resistant Phenotype -> label. 0 = susceptible, 1 = resistant.
PHENOTYPE_MAP = {
    'Susceptible': 0,
    'Susceptible-dose dependent': 0,
    'Resistant': 1,
    'Intermediate': 1,
    'Nonsusceptible': 1,
    'Reduced Susceptibility': 1,
}

# Phenotypes each trainer keeps; the rest of its rows are dropped. They
# differ on purpose, to keep the served models' training data as it was.
LGBM_TRAIN_PHENOTYPES = ('Susceptible', 'Resistant', 'Intermediate', 'Nonsusceptible')
KMER_TRAIN_PHENOTYPES = ('Susceptible', 'Resistant', 'Intermediate')

# MIC comparators a user may type that the forecaster has no category for,
# mapped onto the nearest sign it learned.
MIC_SIGN_ALIASES = {'>=': '>', '\u2265': '>', '\u2264': '<=', '=<': '<=', '=>': '>'}

# Antibiotics offered in the dropdowns, grouped by class. The pages show only
# the names the loaded model knows; this list is the fallback when the backend
# is down, and what GET /api/antibiotics/ returns.
UI_ANTIBIOTICS = [
    'penicillin', 'ampicillin', 'ampicillin/sulbactam', 'amoxicillin',
    'amoxicillin/clavulanic acid', 'piperacillin', 'piperacillin/tazobactam',
    'oxacillin', 'temocillin', 'carbenicillin', 'ticarcillin/clavulanic acid',
    'cefazolin', 'cefoxitin', 'cefotetan', 'cefmetazole', 'cefotaxime',
    'cefotaxime/clavulanic acid', 'ceftazidime', 'ceftazidime/avibactam',
    'ceftazidime/clavulanic acid', 'ceftolozane/tazobactam', 'ceftriaxone',
    'cefepime', 'cefepime/taniborbactam', 'cefuroxime', 'cephalothin',
    'cefixime', 'cefpodoxime', 'cefpodoxime/clavulanic acid', 'ceftibuten',
    'cefoperazone/sulbactam', 'ceftiofur', 'cefpirome', 'cefozopran',
    'ceftaroline', 'ceftobiprole',
    'imipenem', 'imipenem/relebactam', 'meropenem', 'ertapenem', 'doripenem',
    'aztreonam', 'ciprofloxacin', 'levofloxacin', 'norfloxacin',
    'nalidixic acid', 'ofloxacin', 'moxifloxacin', 'pefloxacin',
    'delafloxacin',
    'gentamicin', 'tobramycin', 'amikacin', 'streptomycin', 'neomycin',
    'kanamycin', 'spectinomycin', 'apramycin',
    'tetracycline', 'oxytetracycline', 'doxycycline', 'minocycline',
    'tigecycline',
    'sulfamethoxazole', 'sulfisoxazole', 'trimethoprim',
    'trimethoprim/sulfamethoxazole',
    'chloramphenicol', 'florfenicol',
    'azithromycin', 'erythromycin', 'clarithromycin', 'telithromycin',
    'colistin', 'polymyxin b', 'vancomycin', 'teicoplanin',
    'clindamycin', 'lincomycin', 'nitrofurantoin', 'fosfomycin', 'rifampicin',
]


def normalize_antibiotic(name):
    """Lower-case, strip, and map a spelling variant to its canonical name.

    Names the alias table drops from training (drug classes such as
    'carbapenem') are returned unchanged; a model then reports them as
    unrecognised instead of silently answering for a different drug.
    """
    if name in (None, ''):
        return name
    ab = ' '.join(str(name).split()).lower()
    return ANTIBIOTIC_ALIASES.get(ab) or ab


FRONTEND_COPY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'frontend', 'antibiotic_names.json')


def frontend_names():
    """What the frontend needs, which deploys without backend/."""
    return {
        '_generated_by': 'backend/amr_constants.py; do not edit by hand',
        'antibiotics': UI_ANTIBIOTICS,
        'aliases': ANTIBIOTIC_ALIASES,
    }


if __name__ == '__main__':
    with open(FRONTEND_COPY, 'w', encoding='utf-8') as fh:
        json.dump(frontend_names(), fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    print(f'Wrote {os.path.relpath(FRONTEND_COPY)}')
