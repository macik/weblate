# -*- coding: UTF-8 -*-
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models import Sum
from translate.lang import data

EXTRALANGS = [
    ('ur', 'Urdu', 2, '(n != 1)'),
    ('uz@latin', 'Uzbek (latin)', 1, '0'),
    ('uz', 'Uzbek', 1, '0'),
    ('sr@latin', 'Serbian (latin)', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
    ('sr_RS@latin', 'Serbian (latin)', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
    ('sr@cyrillic', 'Serbian (cyrillic)', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
    ('sr_RS@cyrillic', 'Serbian (cyrillic)', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
    ('be@latin', 'Belarusian (latin)', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
    ('en_US', 'English (United States)', 2, '(n != 1)'),
    ('nb_NO', 'Norwegian Bokmål', 2, '(n != 1)'),
    ('pt_PT', 'Portuguese (Portugal)', 2, '(n > 1)'),
]

class LanguageManager(models.Manager):
    def auto_create(self, code):
        '''
        Autmatically creates new language based on code and best guess
        of parameters.
        '''
        # Create standard language
        lang = Language.objects.create(
            code = code,
            name = '%s (generated)' % code,
            nplurals = 2,
            pluralequation = '(n != 1)',
        )
        # In case this is just a different variant of known language, get params from that
        if '_' in code:
            try:
                baselang = Language.objects.get(code = code.split('_')[0])
                lang.name = '%s (generated - %s)' % (
                    baselang.name,
                    code,
                )
                lang.nplurals = baselang.nplurals
                lang.pluralequation = baselang.pluralequation
                lang.save()
            except Language.DoesNotExist:
                pass
        return lang

    def setup(self, update):
        for code, props in data.languages.items():
            lang, created = Language.objects.get_or_create(
                code = code)
            if not update and not created:
                continue
            lang.name = props[0].split(';')[0]
            # Use shorter name
            if code == 'ia':
                lang.name = 'Interlingua'
            # Shorten name
            elif code == 'el':
                lang.name = 'Greek'
            elif code == 'st':
                lang.name = 'Sotho'
            elif code == 'oc':
                lang.name = 'Occitan'
            elif code == 'nb':
                lang.name = 'Norwegian Bokmål'
            if code == 'gd' and props[2] == 'nplurals=4; plural=(n==1 || n==11) ? 0 : (n==2 || n==12) ? 1 : (n > 2 && n < 20) ? 2 : 3':
                # Workaround bug in data
                lang.nplurals = 4
                lang.pluralequation = '(n==1 || n==11) ? 0 : (n==2 || n==12) ? 1 : (n > 2 && n < 20) ? 2 : 3'
            elif code == 'kk':
                # Kazakh should have plurals, ttkit says it does not have
                lang.nplurals = 2
                lang.pluralequation = '(n != 1)'
            else:
                lang.nplurals = props[1]
                lang.pluralequation = props[2]
            lang.save()
        for props in EXTRALANGS:
            lang, created = Language.objects.get_or_create(
                code = props[0])
            if not update and not created:
                continue
            lang.name = props[1]
            lang.nplurals = props[2]
            lang.pluralequation = props[3]
            lang.save()


class Language(models.Model):
    code = models.SlugField(unique = True)
    name = models.CharField(max_length = 100)
    nplurals = models.SmallIntegerField(default = 0)
    pluralequation = models.CharField(max_length = 255, blank = True)

    objects = LanguageManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return _(self.name)

    def get_plural_form(self):
        return 'nplurals=%d; plural=%s;' % (self.nplurals, self.pluralequation)

    def get_plural_label(self, idx):
        '''
        Returns label for plural form.
        '''
        if idx == 0:
            return _('Singular')
        if self.pluralequation in ['(n != 1)', '(n > 1)', 'n > 1']:
            return _('Plural')
        return _('Plural form %d') % idx

    @models.permalink
    def get_absolute_url(self):
        return ('trans.views.show_language', (), {
            'lang': self.code
        })

    def has_translations(self):
        from trans.models import Translation
        return Translation.objects.filter(language = self).count() > 0

    def get_translated_percent(self):
        from trans.models import Translation
        translations = Translation.objects.filter(language = self).aggregate(Sum('translated'), Sum('total'))
        return round(translations['translated__sum'] * 100.0 / translations['total__sum'], 1)
