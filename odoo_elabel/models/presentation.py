"""Whitelisted immutable e-label presentation; no live product exposed publicly."""
import hashlib
import json
from odoo.tools.misc import formatLang

CONTENT_FIELDS = (
    'elabel_ingredients', 'elabel_allergen_statement', 'elabel_additional_substances',
    'elabel_nutrition_note', 'elabel_energy_kj', 'elabel_energy_kcal', 'elabel_fat',
    'elabel_saturates', 'elabel_carbohydrate', 'elabel_sugars', 'elabel_protein', 'elabel_salt',
)
TEXT_FIELDS = CONTENT_FIELDS[:4]
NUMBER_FIELDS = CONTENT_FIELDS[4:]

def digest(payload):
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()

class LabelPresentation:
    def __init__(self, revision, lang):
        payload = revision.payload
        translations = payload['translations']
        self.lang = lang if lang in translations else next(iter(translations))
        self.env = revision.env(context=dict(revision.env.context, lang=self.lang))
        self.display_name = translations[self.lang]['name']
        for field in TEXT_FIELDS:
            setattr(self, field, translations[self.lang].get(field) or '')
        for field in NUMBER_FIELDS:
            setattr(self, field, payload['numbers'].get(field, 0.0))

    def _get_elabel_display_labels(self):
        return {k: self.env._(v) for k, v in {
            'language':'Language', 'title': 'Wine e-Label', 'nutrition_declaration': 'Nutrition declaration',
            'information_per_100_ml': 'Information per 100 ml', 'ingredients': 'Ingredients',
            'allergens': 'Allergens', 'additional_substances': 'Additional substances',
            'mandatory_information_only': 'This page contains mandatory e-label information only.',
        }.items()}

    def _get_elabel_nutrition_lines(self):
        def fmt(v):
            return formatLang(self.env, v, digits=2)
        return [
            {'label': self.env._('Energy'), 'value': '%s kJ / %s kcal' %
             (fmt(self.elabel_energy_kj), fmt(self.elabel_energy_kcal))},
        ] + [{'label': self.env._(label), 'value': '%s g' % fmt(getattr(self, field))}
             for field, label in [
                 ('elabel_fat', 'Fat'), ('elabel_saturates', 'of which saturates'),
                 ('elabel_carbohydrate', 'Carbohydrate'), ('elabel_sugars', 'of which sugars'),
                 ('elabel_protein', 'Protein'), ('elabel_salt', 'Salt')]]
