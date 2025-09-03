from flask import Flask, request, render_template
from classifier import classify_legal_query
import csv
import os
from datetime import datetime


app = Flask(__name__)
LOG_FILE = 'query_log.csv'

#add your dictionary here
CATEGORY_TRANSLATIONS = {
    "Droit de la famille": "Family Law",
    "Droit immobilier": "Housing Law", 
    "Droit financier": "Financial Law",
    "Droit pénal": "Justice and Criminal Law",
    "Droit des étrangers": "Immigration Law",
    "Droit de la protection sociale": "Social Protection Law",
    "Droit du travail": "Employment Law"
}
fr_LEGAL_RESOURCES = {
    "Droit de la famille": {
        "title": "Ressources en Droit de la Famille",
        "links": [
            {"name": "Loi sur le divorce / Divorce Act", "url": "https://laws-lois.justice.gc.ca/fra/lois/d-3.4/"},
            {"name": "Droit de la famille Ontario / Family Law Ontario", "url": "https://www.ontario.ca/fr/page/droit-de-la-famille"},
            {"name": "Justice Canada - Droit de la famille", "url": "https://www.justice.gc.ca/fra/df-fl/"},
            {"name": "Aide juridique Ontario - Droit de la famille", "url": "https://www.legalaid.on.ca/fr/services/droit-de-la-famille/"},
            {"name": "Tribunal de la famille", "url": "https://www.ontariocourts.ca/ocj/fr/"}
        ]
    },
    "Droit immobilier": {
        "title": "Ressources en Droit immobilier", 
        "links": [
            {"name": "Loi sur la location résidentielle / Residential Tenancies Act", "url": "https://www.ontario.ca/fr/lois/loi/06r17"},
            {"name": "Commission du logement locatif / Landlord and Tenant Board", "url": "https://tribunalsontario.ca/ltb/"},
            {"name": "Droits des locataires Ontario", "url": "https://www.ontario.ca/fr/page/droits-des-locataires"},
            {"name": "FRAPRU - Défense des droits en logement", "url": "https://www.frapru.qc.ca/"},
            {"name": "Régie du logement Québec", "url": "https://www.tal.gouv.qc.ca/fr"}
        ]
    },
    "Droit financier": {
        "title": "Ressources en Droit financier",
        "links": [
            {"name": "Loi sur la protection du consommateur", "url": "https://www.ontario.ca/fr/lois/loi/02c30"},
            {"name": "Bureau du surintendant des institutions financières", "url": "https://www.osfi-bsif.gc.ca/fra/"},
            {"name": "Agence de la consommation en matière financière", "url": "https://www.canada.ca/fr/agence-consommation-matiere-financiere.html"},
            {"name": "Loi sur la faillite et l'insolvabilité", "url": "https://laws-lois.justice.gc.ca/fra/lois/b-3/"},
            {"name": "Commission des services financiers de l'Ontario", "url": "https://www.fsco.gov.on.ca/fr/"}
        ]
    },
    "Droit pénal": {
        "title": "Ressources en Droit pénal",
        "links": [
            {"name": "Code criminel du Canada", "url": "https://laws-lois.justice.gc.ca/fra/lois/c-46/"},
            {"name": "Charte canadienne des droits et libertés", "url": "https://laws-lois.justice.gc.ca/fra/const/page-12.html"},
            {"name": "Cour suprême du Canada", "url": "https://www.scc-csc.ca/home-accueil-fra.aspx"},
            {"name": "Aide juridique Ontario - Droit criminel", "url": "https://www.legalaid.on.ca/fr/services/droit-criminel/"},
            {"name": "Tribunaux de l'Ontario", "url": "https://www.ontariocourts.ca/ocj/fr/"},
            {"name": "Association du Barreau canadien", "url": "https://www.cba.org/"}
        ]
    },
    "Droit des étrangers": {
        "title": "Ressources en Droit des étrangers ",
        "links": [
            {"name": "Loi sur l'immigration et la protection des réfugiés", "url": "https://laws-lois.justice.gc.ca/fra/lois/i-2.5/"},
            {"name": "Immigration, Réfugiés et Citoyenneté Canada", "url": "https://www.canada.ca/fr/immigration-refugies-citoyennete.html"},
            {"name": "Commission de l'immigration et du statut de réfugié", "url": "https://irb-cisr.gc.ca/fr/"},
            {"name": "Aide juridique Ontario - Immigration", "url": "https://www.legalaid.on.ca/fr/services/droit-immigration-refugies/"},
            {"name": "Table de concertation des organismes au service des personnes réfugiées et immigrantes", "url": "https://tcri.qc.ca/"}
        ]
    },
    "Droit de la protection sociale": {
        "title": "Ressources en Droit de la protection sociale",
        "links": [
            {"name": "Loi canadienne sur la santé", "url": "https://laws-lois.justice.gc.ca/fra/lois/c-6/"},
            {"name": "Régime de pensions du Canada", "url": "https://www.canada.ca/fr/services/prestations/pensionspubliques/rpc.html"},
            {"name": "Assurance-emploi", "url": "https://www.canada.ca/fr/services/prestations/ae.html"},
            {"name": "Programme Ontario au travail", "url": "https://www.ontario.ca/fr/page/aide-sociale-ontario-au-travail"},
            {"name": "Sécurité de la vieillesse", "url": "https://www.canada.ca/fr/services/prestations/pensionspubliques/rpc/securite-vieillesse.html"},
            {"name": "Prestations pour enfants", "url": "https://www.canada.ca/fr/agence-revenu/services/prestations-enfants-familles.html"}
        ]
    },
    "Droit du travail": {
        "title": "Ressources en Droit du Travail",
        "links": [
            {"name": "Code canadien du travail", "url": "https://laws-lois.justice.gc.ca/fra/lois/l-2/"},
            {"name": "Loi sur les normes d'emploi (Ontario)", "url": "https://www.ontario.ca/fr/lois/loi/00e41"},
            {"name": "Ministère du Travail - Normes d'emploi", "url": "https://www.ontario.ca/fr/page/normes-demploi"},
            {"name": "Code des droits de la personne", "url": "https://www.ohrc.on.ca/fr/le-code-des-droits-de-la-personne-de-lontario"},
            {"name": "Commission des relations de travail Ontario", "url": "https://www.olrb.gov.on.ca/"},
            {"name": "Santé et sécurité au travail", "url": "https://www.ontario.ca/fr/page/sante-et-securite-au-travail"}
        ]
    }
}

en_LEGAL_RESOURCES = {
    "Droit de la famille": {
        "title": "Family Law Resources",
        "links": [
            {"name": "Divorce Act", "url": "https://laws-lois.justice.gc.ca/fra/lois/d-3.4/"},
            {"name": "Family Law Ontario", "url": "https://www.ontario.ca/fr/page/droit-de-la-famille"},
            {"name": "Justice Canada - Family Law", "url": "https://www.justice.gc.ca/fra/df-fl/"},
            {"name": "Legal Aid Ontario - Family Law", "url": "https://www.legalaid.on.ca/fr/services/droit-de-la-famille/"},
            {"name": "Family Court", "url": "https://www.ontariocourts.ca/ocj/fr/"}
        ]
    },
    "Droit immobilier": {
        "title": "Housing Law Resources", 
        "links": [
            {"name": "Residential Tenancies Act", "url": "https://www.ontario.ca/fr/lois/loi/06r17"},
            {"name": "Landlord and Tenant Board", "url": "https://tribunalsontario.ca/ltb/"},
            {"name": "Ontario Tenants' Rights", "url": "https://www.ontario.ca/fr/page/droits-des-locataires"},
            {"name": "FRAPRU - Housing Rights Advocacy", "url": "https://www.frapru.qc.ca/"},
            {"name": "Québec Rental Board", "url": "https://www.tal.gouv.qc.ca/fr"}
        ]
    },
    "Droit financier": {
        "title": "Financial and Legal Resources",
        "links": [
            {"name": "Consumer Protection Act", "url": "https://www.ontario.ca/fr/lois/loi/02c30"},
            {"name": "Office of the Superintendent of Financial Institutions", "url": "https://www.osfi-bsif.gc.ca/fra/"},
            {"name": "Financial Consumer Agency of Canada", "url": "https://www.canada.ca/fr/agence-consommation-matiere-financiere.html"},
            {"name": "Bankruptcy and Insolvency Act", "url": "https://laws-lois.justice.gc.ca/fra/lois/b-3/"},
            {"name": "Ontario Financial Services Commission", "url": "https://www.fsco.gov.on.ca/fr/"}
        ]
    },
    "Droit pénal": {
        "title": "Justice System Resources",
        "links": [
            {"name": "Canadian Criminal Code", "url": "https://laws-lois.justice.gc.ca/fra/lois/c-46/"},
            {"name": "Canadian Charter of Rights and Freedoms", "url": "https://laws-lois.justice.gc.ca/fra/const/page-12.html"},
            {"name": "Supreme Court of Canada", "url": "https://www.scc-csc.ca/home-accueil-fra.aspx"},
            {"name": "Legal Aid Ontario - Criminal Law", "url": "https://www.legalaid.on.ca/fr/services/droit-criminel/"},
            {"name": "Ontario Courts", "url": "https://www.ontariocourts.ca/ocj/fr/"},
            {"name": "Canadian Bar Association", "url": "https://www.cba.org/"}
        ]
    },
    "Droit des étrangers": {
        "title": "Immigration Resources",
        "links": [
            {"name": "Immigration and Refugee Protection Act", "url": "https://laws-lois.justice.gc.ca/fra/lois/i-2.5/"},
            {"name": "Immigration, Refugees and Citizenship Canada", "url": "https://www.canada.ca/fr/immigration-refugies-citoyennete.html"},
            {"name": "Immigration and Refugee Board of Canada", "url": "https://irb-cisr.gc.ca/fr/"},
            {"name": "Legal Aid Ontario - Immigration", "url": "https://www.legalaid.on.ca/fr/services/droit-immigration-refugies/"},
            {"name": "Table of Refugee and Immigrant Service Organizations", "url": "https://tcri.qc.ca/"}
        ]
    },
    "Droit de la protection sociale": {
        "title": "Social Protection Resources",
        "links": [
            {"name": "Canada Health Act", "url": "https://laws-lois.justice.gc.ca/fra/lois/c-6/"},
            {"name": "Canada Pension Plan", "url": "https://www.canada.ca/fr/services/prestations/pensionspubliques/rpc.html"},
            {"name": "Employment Insurance", "url": "https://www.canada.ca/fr/services/prestations/ae.html"},
            {"name": "Ontario Works Program", "url": "https://www.ontario.ca/fr/page/aide-sociale-ontario-au-travail"},
            {"name": "Old Age Security", "url": "https://www.canada.ca/fr/services/prestations/pensionspubliques/rpc/securite-vieillesse.html"},
            {"name": "Child Benefits", "url": "https://www.canada.ca/fr/agence-revenu/services/prestations-enfants-familles.html"}
        ]
    },
    "Droit du travail": {
        "title": "Employment Law Resources",
        "links": [
            {"name": "Canada Labour Code", "url": "https://laws-lois.justice.gc.ca/fra/lois/l-2/"},
            {"name": "Employment Standards Act (Ontario)", "url": "https://www.ontario.ca/fr/lois/loi/00e41"},
            {"name": "Ministry of Labour - Employment Standards", "url": "https://www.ontario.ca/fr/page/normes-demploi"},
            {"name": "Human Rights Code", "url": "https://www.ohrc.on.ca/fr/le-code-des-droits-de-la-personne-de-lontario"},
            {"name": "Ontario Labour Relations Board", "url": "https://www.olrb.gov.on.ca/"},
            {"name": "Occupational Health and Safety", "url": "https://www.ontario.ca/fr/page/sante-et-securite-au-travail"}
        ]
    }
}
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'query', 'prediction', 'confidence', 'language'])


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    text = request.form.get('text', '')  

    if not text:
        return render_template('index.html', result={'error': 'No text provided'})

    try:
        result = classify_legal_query(text)
    except Exception as e:
        return render_template('index.html', result={'error': f'Error: {str(e)}'})

    #log the query
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text, result['prediction'], result['confidence'], result['language']])
    # Get relevant legal resources using French category name
    french_category = result['prediction']
    english_translation = CATEGORY_TRANSLATIONS.get(french_category, french_category)

    # Determine display category and resources based on query language
    if result['language'] == 'en':
        display_category = english_translation
        display_resources = en_LEGAL_RESOURCES.get(french_category, {})
    else:
        display_category = french_category
        display_resources = fr_LEGAL_RESOURCES.get(french_category, {})

    

    

    # Pass result to template to display
    return render_template('index.html', result={
        'query': text,
        'category': display_category,
        'confidence': result['confidence'],
        'language': result['language'],
        'resources': display_resources
    })

if __name__ == '__main__':
    app.run(debug=True)
