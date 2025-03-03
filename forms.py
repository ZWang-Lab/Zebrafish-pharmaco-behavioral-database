#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 11 08:05:03 2023

@author: hill103

this script defines forms used in Drug Search page
"""



from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField, RadioField, HiddenField
from wtforms.validators import InputRequired



class form_combined(FlaskForm):
    '''forms used in Drug Search page and Show Data page
    '''
    
    # a multi select form for Drug Name
    drug_name = SelectMultipleField('Drug Name',
                                  choices=[],
                                  validators=[InputRequired()])
    
    # a multi select form for Sleep Wake Features
    sleepwake_feature = SelectMultipleField('Sleep Wake',
                                  choices=[],
                                  validators=[InputRequired()])
    
    # a multi select form for Startle Features
    startle_feature = SelectMultipleField('Startle',
                                  choices=[],
                                  validators=[InputRequired()])
    
    # a radio form for value type (p value or scaled beta)
    value_type = RadioField('Value Type',
                            choices=[('p_value', 'p value'),
                                     ('beta', 'scaled beta')],
                            validators=[InputRequired()],
                            default='p_value')
    
    # two buttons to submit request
    heatmap_button = SubmitField('Draw Heatmap')
    value_button = SubmitField('Browse Data')
    
    # forms for show heatmap, now we combined them into drug search page
    # a hidden input form to receive selected drugs
    hidden_drug_name = HiddenField(default='')
    
    # a hidden input form to receive selected features
    hidden_feature_name = HiddenField(default='')
    
    # a hidden input form to indicate it's p value or scaled beta
    hidden_value_type = HiddenField(default='')