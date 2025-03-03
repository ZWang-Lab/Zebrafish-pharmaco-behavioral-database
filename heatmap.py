#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 29 21:40:20 2023

@author: hill103

this script defines custom functions to generate Heatmap using Clustergrammer-PY (https://github.com/MaayanLab/clustergrammer-py)

we change the settings to be consistent with R package `pheatmap`

we also define custom functions to handle missing values in pairwise distance calculation
"""



import numpy as np
from copy import deepcopy
from clustergrammer import Network, initialize_net, calc_clust, categories, cat_pval, make_viz



def custom_euclidean(u, v):
    # Compute Euclidean distance between vectors u and v, ignoring dimensions with NaN
    # Get mask where neither u nor v is NaN
    mask = ~np.isnan(u) & ~np.isnan(v)
    
    # Compute the squared differences using the mask
    dist_squared = np.sum((u[mask] - v[mask])**2)
    
    # Return the Euclidean distance
    return np.sqrt(dist_squared)


def custom_pdist(mat, metric):
    # Compute pairwise distances using custom metric
    n = mat.shape[0]
    result = []
    for i in range(n):
        for j in range(i+1, n):
            result.append(metric(mat[i], mat[j]))
    return np.array(result)


def custom_calc_distance_matrix(tmp_mat, inst_rc, dist_type='euclidean'):
    # a custom function of Clustergrammer-py to call the distance calculation with support for missing values
    if dist_type == 'euclidean':
        dist_func = custom_euclidean
    else:
        raise ValueError(f"Unsupported distance type: {dist_type}")
    
    if inst_rc == 'row':
        inst_dm = custom_pdist(tmp_mat, metric=dist_func)
    elif inst_rc == 'col':
        inst_dm = custom_pdist(tmp_mat.transpose(), metric=dist_func)
    
    inst_dm[inst_dm < 0] = float(0)
    
    return inst_dm


def custom_cluster_row_and_col(net, dist_type='cosine', linkage_type='average',
                        dendro=True, run_clustering=True, run_rank=True,
                        ignore_cat=False, calc_cat_pval=False, links=False):
    # a custom function of Clustergrammer-py adding support for missing values
    dm = {}
    for inst_rc in ['row', 'col']:
  
        tmp_mat = deepcopy(net.dat['mat'])
        dm[inst_rc] = custom_calc_distance_matrix(tmp_mat, inst_rc, dist_type)
    
        # save directly to dat structure
        node_info = net.dat['node_info'][inst_rc]
    
        node_info['ini'] = list(range(len(net.dat['nodes'][inst_rc]), -1, -1))
    
        # cluster
        if run_clustering is True:
            node_info['clust'], node_info['group'] = \
                calc_clust.clust_and_group(net, dm[inst_rc], linkage_type=linkage_type)
        else:
            dendro = False
            node_info['clust'] = node_info['ini']
    
        # sorting
        if run_rank is True:
            node_info['rank'] = calc_clust.sort_rank_nodes(net, inst_rc, 'sum')
            node_info['rankvar'] = calc_clust.sort_rank_nodes(net, inst_rc, 'var')
        else:
            node_info['rank'] = node_info['ini']
            node_info['rankvar'] = node_info['ini']
    
        if ignore_cat is False:
            categories.calc_cat_clust_order(net, inst_rc)
  
    if calc_cat_pval is True:
        cat_pval.main(net)
  
    # make the visualization json
    make_viz.viz_json(net, dendro, links)
  
    return dm


def filter_df(df):
    # remove rows or columns with all NaN
    return df.dropna(axis=0, how='all').dropna(axis=1, how='all')


def generate_heatmap_json(df):
    # generate a Visualization-JSON for use by Clustergrammer-JS in front end
    # return it as a string
    
    # make network object and load DataFrame, df
    net = Network()
    net.load_df(df)
    
    # NOTE: a custom pipeline to create a dendrogram that highlights the hierarchical clustering of BOTH the columns and rows
    # manually disable ALL filtering
    initialize_net.viz(net)
    
    # the settings are consistent with R package `pheatmap`
    custom_cluster_row_and_col(net, dist_type='euclidean', linkage_type='complete', run_clustering=True,
                               dendro=True, ignore_cat=False, calc_cat_pval=False)
    
    net.sim = {}
    net.viz['views'] = []

    # exported as a string
    return net.export_net_json('viz', indent='no-indent')