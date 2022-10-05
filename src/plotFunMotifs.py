'''
Created on 17 Nov 2017

@author: husensofteng
'''
import matplotlib
matplotlib.use('Agg')
from matplotlib.pyplot import tight_layout
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import pandas as pd
import numpy as np
import seaborn as sns
import psycopg2
sns.set_style("white")
#from multiprocessing import Pool
import multiprocessing as mp
from pybedtools import BedTool
#plt.style.use('ggplot')
#sns.set_context("paper")#talk
#plt.style.use('seaborn-ticks')

params = {'-sep': '\t', 
          '-cols_to_retrieve':'chr, motifstart, motifend, strand, name, score, pval, fscore, chromhmm, contactingdomain, dnase__seq, fantom, loopdomain, numothertfbinding, othertfbinding, replidomain, tfbinding, tfexpr', '-number_rows_select':'all',
          '-restart_conn_after_n_queries':100000, '-variants':True, '-regions':True,
          '-chr':0, '-start':1, '-end':2, '-ref':3, '-alt':4, 
          '-db_name':'funmotifsdbtest', '-db_host':'localhost', '-db_port':5432, '-db_user':'huum', '-db_password':'',
          '-all_motifs':True, '-motifs_tfbining':False, '-max_score_motif':False, '-motifs_tfbinding_otherwise_max_score_motif':False,
          '-verbose': True}

def get_params(params_list, params_without_value):
    global params
    for i, arg in enumerate(params_list):#priority is for the command line
        if arg.startswith('-'): 
            if arg in params_without_value:
                params[arg] = True
            else:
                try:
                    v = params_list[i+1]
                    if v.lower()=='yes' or v.lower()=='true':
                        v=True
                    elif v.lower()=='no' or v.lower()=='false':
                        v=False
                    params[arg] =  v
                except IndexError:
                    print("no value is given for parameter: ", arg )
    return params

def open_connection():
    conn = psycopg2.connect("dbname={} user={} password={} host={} port={}".format(params['-db_name'], params['-db_user'], params['-db_password'], params['-db_host'], params['-db_port']))
    return conn
    
def plot_motif_freq(tfs, tissue_tables, motifs_table, min_fscore, fig_name):
    
    conn = open_connection()
    curs = conn.cursor()
    fig = plt.figure(figsize=(6*len(tissue_tables),10))
    gs = gridspec.GridSpec(len(tissue_tables), 1, wspace=0.0, hspace=0.0)#height_ratios=[4,2], width_ratios=[4,2], wspace=0.0, hspace=0.0)#create 4 rows and three columns with the given ratio for each
    
    for i,tissue_table in enumerate(tissue_tables):
        tfs_freq = []
        for tf_name in tfs:    
            stmt_all = "select count({tissue}.mid) from {motifs},{tissue} where {motifs}.mid={tissue}.mid and {motifs}.name like '%{tf_name}%'".format(motifs=motifs_table, tissue=tissue_table, tf_name=tf_name)
            print(stmt_all)
            stmt_tfbinding = "select count({tissue}.mid) from {motifs},{tissue} where {motifs}.mid={tissue}.mid and {motifs}.name like '%{tf_name}%' and ({tissue}.tfbinding>0 and {tissue}.tfbinding!='NaN')".format(motifs=motifs_table, tissue=tissue_table,tf_name=tf_name)
            stmt_dnase = "select count({tissue}.mid) from {motifs},{tissue} where {motifs}.mid={tissue}.mid and {motifs}.name like '%{tf_name}%' and ({tissue}.dnase__seq>0 and {tissue}.dnase__seq!='NaN')".format(motifs=motifs_table, tissue=tissue_table, tf_name=tf_name)
            stmt_active = "select count({tissue}.mid) from {motifs},{tissue} where {motifs}.mid={tissue}.mid and tfexpr>0 and {motifs}.name like '%{tf_name}%' and ((fscore>{min_fscore} and dnase__seq>0 and dnase__seq!='NaN' and (tfbinding>0 or {tissue}.tfbinding='NaN')) or (tfbinding>0 and {tissue}.tfbinding!='NaN' and {tissue}.dnase__seq>0))".format(motifs=motifs_table, tissue=tissue_table, tf_name=tf_name, min_fscore=min_fscore)
            curs.execute(stmt_all)
            motifs_all = curs.fetchall()
            curs.execute(stmt_tfbinding)
            tfbinding = curs.fetchall()
            curs.execute(stmt_dnase)
            dnase = curs.fetchall()
            curs.execute(stmt_active)
            active = curs.fetchall()
            tfs_freq.extend([[tf_name, tissue_table, 'All Motifs', int(motifs_all[0][0])], 
                    [tf_name, tissue_table, 'DHSs', int(dnase[0][0])], 
                    [tf_name, tissue_table, 'Matching TFBSs', int(tfbinding[0][0])], 
                    [tf_name, tissue_table, 'Functional Motifs', int(active[0][0])]])
        
        df = pd.DataFrame(tfs_freq, columns = ['TFs', 'Tissue', 'Activity', 'Number of motifs'])
        #df['Number of motifs'] = df['Number of motifs'].apply(np.log2)
        ax = fig.add_subplot(gs[i, 0])
        s = sns.barplot(x='TFs', y='Number of motifs', hue='Activity', data=df, estimator=sum, ax=ax)
        s.set(ylabel='Number of motifs (log2)', xlabel='')
        ax.legend_.remove()
        sns.despine(right=True, top=True, bottom=False, left=False)
    curs.close()
    plt.legend(bbox_to_anchor=(1, 1), loc=4)
    gs.tight_layout(fig, pad=1, h_pad=2.0, w_pad=0.0)
    plt.savefig(fig_name+'.pdf')
    plt.savefig(fig_name+'.svg')
    plt.close()
    
    
def plot_fscore(tf_name, tissue_table, motifs_table, tissue_names, fig_name):
    
    conn = open_connection()
    curs = conn.cursor()
    
    stmt_all = "select {tissue_names} from {motifs},{tissue} where {motifs}.mid={tissue}.mid and {motifs}.name like '%{tf_name}%'".format(
        tissue_names=','.join(sorted(tissue_names)), motifs=motifs_table, tissue=tissue_table, tf_name=tf_name)
    print(stmt_all)
    curs.execute(stmt_all)
    scores_all = curs.fetchall()
    curs.close()
    df = pd.DataFrame(scores_all, columns=tissue_names)
    s = sns.boxplot(data=df, color='grey')
    ss = s.get_figure()
    ss.savefig(fig_name+'.pdf', bbox_inches='tight')
    ss.savefig(fig_name+'.svg', bbox_inches='tight')
    return

def plot_fscore_all(ax, table_name, motifs_table, tissue_names, fig_name):
    
    conn = open_connection()
    curs = conn.cursor()
    
    stmt_all = "select {tissue_names} from {table_name},{motifs} where {motifs}.mid={table_name}.mid and {motifs}.chr=1".format(
        tissue_names=','.join(tissue_names), table_name=table_name, motifs=motifs_table)
    print(stmt_all)
    curs.execute(stmt_all)
    scores_all = curs.fetchall()
    curs.close()
    df = pd.DataFrame(scores_all, columns=tissue_names)
    print(df.head())
    
    sns.swarmplot(data=df, ax=ax, color='grey', linewidth=0.5)
    sns.despine(right=True, top=True, bottom=False, left=False)
    ax.set_xlabel('')
    ax.set_ylabel('Functionality Scores')
    ax.set_ylim(0,5)
    
    return
def plot_fscore_all_selected_tfs(ax, table_name, motifs_table, tissue_names, tfs, fig_name):
    
    conn = open_connection()
    curs = conn.cursor()
    scores_all = []
    for tf in tfs:
        stmt_all = "select {tissue_names} from {table_name},{motifs} where {motifs}.mid={table_name}.mid and {motifs}.name like '%{tf}%'".format(
            tissue_names=','.join(tissue_names), table_name=table_name, motifs=motifs_table, tf=tf)
        print(stmt_all)
        curs.execute(stmt_all)
        tf_scores = curs.fetchall()
        tf_scores_list = pd.DataFrame(tf_scores, columns=tissue_names).stack().tolist()
        print(len(tf_scores_list))
        scores_all.append(tf_scores_list)
    curs.close()
    print(len(scores_all))
    
    sns.swarmplot(data=scores_all, color='grey', ax=ax, linewidth=0.5)
    ax.set_xticklabels(tfs)
    ax.set_xlabel('')
    ax.set_ylabel('Functionality Scores')
    ax.set_ylim(0,5)
    sns.despine(right=True, top=True, bottom=False, left=False)
    
    
def plot_fscores_myloid(ax, table_name, fig_name):
    
    conn = open_connection()
    curs = conn.cursor()
    scores_all = []
    stmts_boundmotifs = "select fscore from {table_name} where tfbinding>0 and tfbinding!='NaN' and dnase__seq>0".format(
        table_name=table_name)
    stmts_unboundmotifs = "select fscore from {table_name} where tfbinding=0 and tfbinding!='NaN'".format(
        table_name=table_name)
    
    print(stmts_boundmotifs)
    curs.execute(stmts_boundmotifs)
    fscores_boundmotifs = curs.fetchall()
    fscores_boundmotifs_list = pd.DataFrame(fscores_boundmotifs, columns=['fscore']).stack().tolist()
    print(len(fscores_boundmotifs_list))
    scores_all.append(fscores_boundmotifs_list)
    
    print(stmts_unboundmotifs)
    curs.execute(stmts_unboundmotifs)
    fscores_unboundmotifs = curs.fetchall()
    fscores_boundmotifs_list = pd.DataFrame(fscores_unboundmotifs, columns=['fscore']).stack().tolist()
    scores_all.append(fscores_boundmotifs_list)
    curs.close()
    
    sns.swarmplot(data=scores_all, color='grey', ax=ax, linewidth=0.5)
    ax.set_xticklabels(['Bound motifs', 'Unbound motifs'])
    ax.set_xlabel('')
    ax.set_ylabel('Functionality Scores')
    ax.set_ylim(0,5)
    sns.despine(right=True, top=True, bottom=False, left=False)
    
def plot_heatmap(motifs_table,tissue_table, fig_name, threshold_to_include_tf, otherconditions):
    conn = open_connection()
    curs = conn.cursor()
    
    stmt_all = "select chromhmm, upper(split_part(name,'_', 1)), count(name) from {motifs},{tissue} where {motifs}.mid={tissue}.mid {otherconditions} group by chromhmm,name order by chromhmm".format(
        motifs=motifs_table, tissue=tissue_table, otherconditions=otherconditions)
    print(stmt_all)
    curs.execute(stmt_all)
    scores_all = curs.fetchall()
    curs.close()
    df = pd.DataFrame(scores_all, columns=['Chromatin States', 'TFs', 'Frequency'])
    df_pivot = df.pivot('Chromatin States', 'TFs', 'Frequency')
    df_pivot_filtered = pd.DataFrame()
    for c in df_pivot.columns:
            if df_pivot[c].sum()>threshold_to_include_tf:
                df_pivot_filtered[c] = df_pivot[c] 
    print(df_pivot_filtered.head())
    if len(df_pivot_filtered)>0:
        s = sns.heatmap(data=df_pivot_filtered, square=True, cbar=True)
        ss = s.get_figure()
        ss.savefig(fig_name+'.pdf', bbox_inches='tight')
        ss.savefig(fig_name+'.svg', bbox_inches='tight')
    
def plot_scatter_plot(motifs_table, tissue_tables, otherconditions, figname):
    conn = open_connection()
    curs = conn.cursor()
    
    dfs = []
    for tissue_table in tissue_tables:
        stmt_all = "select upper(split_part(name,'_', 1)), count(name) as freq from {motifs},{tissue} where {motifs}.mid={tissue}.mid {otherconditions} group by name order by freq desc".format(
            motifs=motifs_table, tissue=tissue_table, otherconditions=otherconditions)
        print(stmt_all)
        curs.execute(stmt_all)
        scores_all = curs.fetchall()
        
        df = pd.DataFrame(scores_all, columns=['TFs', 'Number of Functional Motifs per TF'])
        df['Tissue']=[tissue_table for i in range(0,len(df))]
        dfs.append(df)
    curs.close()
    all_dfs = pd.concat(dfs)
    print(all_dfs.head())
    
    fig = plt.figure(figsize=(13,8))
    s = sns.stripplot(x='Tissue', y='Number of Functional Motifs per TF', data=all_dfs, jitter=True)
    sns.despine(right=True, top=True, bottom=True, left=False)
    s.set(xlabel='', ylabel='Number of motifs', ylim=(0,70000))
    
    for i, r in all_dfs.iterrows():
        if r['Number of Functional Motifs per TF']>=30000:
            print(r)
            print((r['TFs'], (tissue_tables.index(r['Tissue']),r['Number of Functional Motifs per TF']),
                       (tissue_tables.index(r['Tissue']), r['Number of Functional Motifs per TF']+20)))
                       
            s.annotate(r['TFs'], xy=(tissue_tables.index(r['Tissue']),r['Number of Functional Motifs per TF']),
                       xytext=(tissue_tables.index(r['Tissue']), r['Number of Functional Motifs per TF']+4000),rotation=45)
                       
    ss = s.get_figure()
    
    ss.savefig(figname + '.pdf', bbox_inches='tight')
    ss.savefig(figname + '.svg', bbox_inches='tight')
    
    return df

def run_query(query_stmt, tissue_table, cols):
    conn = open_connection()
    curs = conn.cursor()
    curs.execute(query_stmt)
    query_results = curs.fetchall()
    df = pd.DataFrame(query_results, columns=cols)
    print(df.head())
    df.to_csv(tissue_table, sep='\t', index=False)
    df_bed = BedTool.from_dataframe(df).sort().merge(c=[4,5,6,7,8,9],o=['distinct','max', 'distinct', 'max','max', 'distinct'])
    df = BedTool.to_dataframe(df_bed, names=cols)
    df.to_csv(tissue_table+'_merged', sep='\t', index=False)
    print(df.head())
    curs.close()
    conn.close()
    
def get_funmotifs(tissue_tables, otherconditions):
    cols = ['chr', 'motifstart', 'motifend', 'name', 'fscore', 'chromhmm', 'dnase__seq', 'contactingdomain', 'replidomain']
    
    motifs_table = 'motifs'
    p = mp.Pool(8)
    for tissue_table in tissue_tables:
        print(tissue_table)
        query_stmt = "select {cols} from {motifs},{tissue} where {motifs}.mid={tissue}.mid {otherconditions}".format(
            cols=','.join(cols), motifs=motifs_table, tissue=tissue_table, otherconditions=otherconditions)
        print(query_stmt)
        p.apply_async(run_query, args=(query_stmt, tissue_table, cols))
    
    p.close()
    p.join()
    
def plot_freq(file_x, file_y):
    d_x = {}
    d_y = {}
    x = []
    y = []
    names = []
    with open(file_x, 'r') as fx, open(file_y, 'r') as fy:
        for l in fx:
            (k, v) = l.strip().split('\t')
            d_x[k] = int(v)
        for l in fy:
            (k, v) = l.strip().split('\t')
            d_y[k] = int(v)
        if len(d_x.keys()) > len(d_y.keys()):
            for k in d_x.keys():
                x.append(d_x[k])
                names.append(k.split('_')[0])
                try:
                    y.append(d_y[k])
                except KeyError:
                    y.append(0)
        else:
            for k in d_y.keys():
                y.append(d_y[k])
                names.append(k.split('_')[0])
                try:
                    x.append(d_x[k])
                except KeyError:
                    x.append(0)
    
    fig = plt.figure(figsize=(8,5))
    s = sns.regplot(x=np.array(x), y=np.array(y), color='grey')
    sns.despine(right=True, top=True, bottom=True, left=False)
    s.set(ylim=(0,70000),
          xlim=(0,1100000))
    s.set_xlabel(xlabel='Number of sequence motifs')#, fontsize=6)
    s.set_ylabel(ylabel='Number of functional motifs')#, fontsize=6)
    #s.tick_params(labelsize=5)
    
    for i, v in enumerate(y):
        if v>30000:
            s.annotate(names[i], xy=(x[i], v),
                       xytext=(x[i], y[i]+3500),rotation=45)#, fontsize=6)
            
    ss = s.get_figure()
    
    ss.savefig(file_x+"_"+file_y+ '.pdf', bbox_inches='tight')
    ss.savefig(file_x+"_"+file_y+ '.svg', bbox_inches='tight')
    
    return
    
if __name__ == '__main__':
    
    if len(sys.argv)<=0:
        print("Usage: python plotFunMotifs -plot")
        sys.exit(0)
    motifs_table='motifs'
    get_params(sys.argv[1:], params_without_value=[])
    
    tissue_tables= sorted(['blood', 'brain', 'breast','cervix', 'colon', 'esophagus', 'kidney', 'liver', 'lung', 'myeloid', 'pancreas', 'prostate', 'skin', 'stomach', 'uterus'])
    tfs = sorted(['CTCF', 'CEBPB', 'FOXA1', 'MAFK', 'FOS::JUN', 'SP1', 'KLF14'])
    min_fscore = 2.55
    otherconditions = " and tfexpr > 0 and ( (fscore>{min_fscore} and (dnase__seq>0 and dnase__seq!='NaN') and (tfbinding>0 or tfbinding='NaN')) or (tfbinding>0 and tfbinding!='NaN' and dnase__seq>0))".format(
        min_fscore=min_fscore)
    
    #get_funmotifs(sorted(tissue_tables), otherconditions)
    #plot_freq(file_x=sys.argv[1], file_y=sys.argv[2])
    
    #fig2
    #plot_scatter_plot(motifs_table, tissue_tables, otherconditions, figname = 'Number_of_Functional_Motifs_per_TF_annotate')
    
    #fig1
    fig = plt.figure(figsize=(12,8), linewidth=0.5)#design a figure with the given size
    gs = gridspec.GridSpec(2, 4, wspace=1.0, hspace=1.0)#height_ratios=[4,2], width_ratios=[4,2], wspace=0.0, hspace=0.0)#create 4 rows and three columns with the given ratio for each
    ax0 = fig.add_subplot(gs[0, 0:])
    ax1 = fig.add_subplot(gs[1, 0:3])
    ax2 = fig.add_subplot(gs[1, 3])
    plot_fscore_all(ax0, 'all_tissues', motifs_table, tissue_tables, 'all_fscores')
    plot_fscore_all_selected_tfs(ax1, 'all_tissues', motifs_table, tissue_tables, tfs, 'all_fscores_selected_tfs')
    plot_fscores_myloid(ax2, table_name='myeloid', fig_name='bound_unboundmotifs_myeloid')
    gs.tight_layout(fig, pad=1, h_pad=2.0, w_pad=2.0)
    plt.savefig('fig1_swarmplot'+'.pdf')
    plt.savefig('fig1_swarmplot'+'.svg')
    plt.close()
    
    
    #supp fig1
    tissue_tables = sorted(['blood', 'liver', 'myeloid'])
    #plot_motif_freq(tfs, tissue_tables, motifs_table, min_fscore, fig_name='sfig1_barplots_numbmoitfs')
    #heatmap
    tissue_tables = sorted(['blood', 'liver', 'myeloid'])
    threshold_to_include_tf_in_heatmap = 10000
    for tissue_table in tissue_tables:
        fig = plt.figure()#figsize=(12,6))
        #plot_heatmap(motifs_table=motifs_table,tissue_table=tissue_table, fig_name='fig3_heatmap_min10_'+tissue_table, threshold_to_include_tf=threshold_to_include_tf_in_heatmap, otherconditions=otherconditions)
    
    
    if '-fig2' in params.keys():
        print('plotting figure 2')
        for tf in sorted(tfs):
            fig = plt.figure(figsize=(12,6))
            plot_fscore(tf_name=tf, tissue_table='all_tissues', motifs_table=motifs_table, tissue_names=tissue_tables, fig_name='fig2_'+tf)
