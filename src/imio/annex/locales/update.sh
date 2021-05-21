#!/bin/bash
# i18ndude should be available in current $PATH (eg by running
# ``export PATH=$PATH:$BUILDOUT_DIR/bin`` when i18ndude is located in your buildout's bin directory)
#
# For every language you want to translate into you need a
# locales/[language]/LC_MESSAGES/imio.annex.po
# (e.g. locales/de/LC_MESSAGES/imio.annex.po)


domain=imio.annex

i18ndude rebuild-pot --pot $domain.pot --create $domain ../

declare -a languages=("fr")
for lang in "${languages[@]}"; do
		mkdir -p $lang/LC_MESSAGES
done

for lang in $(find . -mindepth 1 -maxdepth 1 -type d); do
		if test -d $lang/LC_MESSAGES; then
				touch $lang/LC_MESSAGES/$domain.po
				touch $lang/LC_MESSAGES/plone.po
				touch $lang/LC_MESSAGES/collective.quickupload.po
				touch $lang/LC_MESSAGES/collective.eeafaceted.batchactions.po
				i18ndude sync --pot $domain.pot $lang/LC_MESSAGES/$domain.po
				i18ndude sync --pot plone.pot $lang/LC_MESSAGES/plone.po
				i18ndude sync --pot collective.quickupload.pot $lang/LC_MESSAGES/collective.quickupload.po
				i18ndude sync --pot collective.eeafaceted.batchactions.pot $lang/LC_MESSAGES/collective.eeafaceted.batchactions.po
		fi
done
