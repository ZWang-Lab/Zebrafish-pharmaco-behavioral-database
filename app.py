#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 03:51:05 2023

@author: hill103

main function
"""



from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask_bootstrap import Bootstrap5
from forms import form_combined
import os
import pandas as pd
import numpy as np
from heatmap import filter_df, generate_heatmap_json



# --------------------Session related ----------------------------------------#
'''
We use session to pass data between routes.

By default, Flask's session object uses a signed cookie to keep the session data client-side. The session data doesn't get automatically cleared after you send or access it. NOTE The size limit is 4KB.

In Flask, the default session mechanism is client-side. When you set values in the session, Flask serializes the data, signs it to prevent tampering (using the app's secret key), and then sends it to the client as a cookie. When a client makes subsequent requests to the server, the cookie containing the session data is sent back to the server. Flask then verifies the signature, deserializes the data, and makes it available in the session object for your views to use.

The use of Base64 encoding in the given context serves as a bridge to convert binary data (like the output from gzip.compress()) into a string representation that is safe for transport.

Even after gzip, the session data still exceed size limit...

Avoid using seesion data!!! So avoid redirecting routes!!! Instead directly make POST request to corresponding routes in front end!!!
'''



# --------------------Flask related ------------------------------------------#
app = Flask(__name__)
app.config.update({'SECRET_KEY': os.environ.get("FLASK_APP_KEY"), 'DEBUG': True, 'SSL_DISABLE': False, 'WTF_CSRF_ENABLED': True})
Bootstrap5(app)



# --------------------Preprocessing related ----------------------------------#
# read csv file, NOTE NA and NaN exist
drug_beta = pd.read_csv(os.path.join(r'./static/csv', 'drug_scaled_beta_774.tsv'), sep='\t', index_col=0)

# score = -log10(pvalue) * direction
drug_score = pd.read_csv(os.path.join(r'./static/csv', 'drug_score_774.tsv'), sep='\t', index_col=0)

# raw pvalue = 10^-abs(score)
drug_pval = 10 ** -np.abs(drug_score)

# dataframes for front end, round to 3 digits and change to string type
drug_beta_frontend = drug_beta.round(3)
drug_pval_frontend = drug_pval.round(3)
# Convert entire DataFrame to string
drug_beta_frontend = drug_beta_frontend.astype(str)
drug_pval_frontend = drug_pval_frontend.astype(str)
# Replace 'nan' with empty string
drug_beta_frontend.replace('nan', '', inplace=True)
drug_pval_frontend.replace('nan', '', inplace=True)



# --------------------Heatmap related ----------------------------------------#
# finally define it as a Flask route
@app.route('/show_heatmap', methods=['GET', 'POST'])
def show_heatmap():
    
    form = form_combined(formdata=request.form)
    
    if request.method == 'GET':
        return render_template('show_heatmap.html',
                               success = False,
                               for_print = 'NO drug and feature selected!',
                               display_heatmap = False)
    
    
    # no validation performed in front end, so DO NOT use form.validate_on_submit()
    if request.method == 'POST':
        # first extract data from form
        if len(form.hidden_drug_name.data)>0 and len(form.hidden_feature_name.data)>0 and len(form.hidden_value_type.data)>0:
            # POST from Show Data page; sent data is string
            drug = form.hidden_drug_name.data.split(';')
            feature = form.hidden_feature_name.data.split(';')
            value_type = form.hidden_value_type.data
        
        else:
            # POST from Drug Search page; sent data is list
            drug = form.drug_name.data
            feature = form.sleepwake_feature.data + form.startle_feature.data
            value_type = form.value_type.data

        
        # slice data; it works even we slice with empty list
        if value_type == 'p_value':
            data_show = drug_score.loc[drug, feature]
        elif value_type == 'beta':
            data_show = drug_beta.loc[drug, feature]
        
        data_show_clean = filter_df(data_show)
        
        # we can only generate heatmap on at least 2 drugs and 2 features
        if data_show_clean.shape[0]<2 and data_show_clean.shape[1]<2:
            return render_template('show_heatmap.html',
                                   success = False,
                                   for_print = 'Generating heatmap requires selecting at least TWO drugs and TWO features. Please select more drugs and features.',
                                   display_heatmap = False)
    
        elif data_show_clean.shape[0] < 2:
            return render_template('show_heatmap.html',
                                   success = False,
                                   for_print = 'Generating heatmap requires selecting at least TWO drugs and TWO features. Please select more drugs.',
                                   display_heatmap = False)
    
        elif data_show_clean.shape[1] < 2:
            return render_template('show_heatmap.html',
                                   success = False,
                                   for_print = 'Generating heatmap requires selecting at least TWO drugs and TWO features. Please select more features.',
                                   display_heatmap = False)
    
        # prepare print message highlighting the removed drugs and/or features
        if value_type == 'p_value':
            for_print = f'Show heatmap on <i>drug scores</i> of {data_show_clean.shape[0]} drugs and {data_show_clean.shape[1]} features.'
        elif value_type == 'beta':
            for_print = f'Show heatmap on <i>scaled beta values</i> of {data_show_clean.shape[0]} drugs and {data_show_clean.shape[1]} features.'
        
        if data_show_clean.shape[0]<data_show.shape[0] and data_show_clean.shape[1]<data_show.shape[1]:
            for_print += f'\nNOTE removed {data_show.shape[0]-data_show_clean.shape[0]} drugs and {data_show.shape[1]-data_show_clean.shape[1]} features due to all values being missing.'
        elif data_show_clean.shape[0] < data_show.shape[0]:
            for_print += f'\nNOTE removed {data_show.shape[0]-data_show_clean.shape[0]} drugs due to all values being missing.'
        elif data_show_clean.shape[1] < data_show.shape[1]:
            for_print += f'\nNOTE removed {data_show.shape[1]-data_show_clean.shape[1]} features due to all values being missing.'
        
        return render_template('show_heatmap.html',
                               success = True,
                               for_print = for_print,
                               display_heatmap = True,
                               json_str = generate_heatmap_json(data_show_clean))



# --------------------Display table related ----------------------------------#
# finally define it as a Flask route
@app.route('/show_data', methods=['GET', 'POST'])
def show_data():
    
    form = form_combined(formdata=request.form)
    
    if request.method == 'GET':
        return render_template('show_data_beta.html',
                               success = False,
                               for_print = 'NO drug and feature selected!',
                               display_table = False,
                               active_page = 'search')
    
    
    # no validation performed in front end, so DO NOT use form.validate_on_submit()
    if request.method == 'POST':
        # first extract data from form
        # only accept POST from Drug Search page; sent data is list
        drug = form.drug_name.data
        feature = form.sleepwake_feature.data + form.startle_feature.data
        value_type = form.value_type.data
        
        # first check: at least 1 drug and 1 feature are selected
        if len(drug) == 0:
            # no drug selected
            return render_template('show_data_beta.html',
                                   success = False,
                                   for_print = 'No drug selected! Please select at least ONE drug!',
                                   display_table = False,
                                   active_page = 'search')
        
        if len(feature) == 0:
            # no feature selected
            return render_template('show_data_beta.html',
                                   success = False,
                                   for_print = 'No behavioral feature selected! Please select at least ONE feature!',
                                   display_table = False,
                                   active_page = 'search')
        
        
        # render different templates according to the value_type
        if value_type == 'p_value':
            data_show = drug_pval_frontend.loc[drug, feature]
            return render_template('show_data_pval.html',
                                   success = True,
                                   for_print = f'Show <i>p values</i> of {data_show.shape[0]} drugs and {data_show.shape[1]} features.',
                                   display_table = True,
                                   col_names = data_show.columns,
                                   data = [[index] + row.tolist() for index, row in data_show.iterrows()],
                                   form = form,
                                   active_page='search')
    
        elif value_type == 'beta':
            data_show = drug_beta_frontend.loc[drug, feature]
            return render_template('show_data_beta.html',
                                   success = True,
                                   for_print = f'Show <i>scaled beta values</i> of {data_show.shape[0]} drugs and {data_show.shape[1]} features.',
                                   display_table = True,
                                   col_names = data_show.columns,
                                   data = [[index] + row.tolist() for index, row in data_show.iterrows()],
                                   form = form,
                                   active_page='search')



# --------------------Webpage related ----------------------------------------#
# Home page
@app.route('/')
def index():
    return render_template('index.html', active_page='home')

# Drug Search page
# UPDATE: not accept POST anymore; POST to other routes in front end instead
@app.route('/search_drug', methods=['GET'])
def search_drug():
    
    form = form_combined(formdata=request.form)
    
    if request.method == 'GET':
        return render_template('search_drug.html', form=form, active_page='search')

# Team page
@app.route('/team')
def show_team():
    return render_template('team.html', active_page='team')



if __name__ == '__main__':
    # use internal IP
    app.run(host=os.environ.get("INTERNAL_IP"), port=80)