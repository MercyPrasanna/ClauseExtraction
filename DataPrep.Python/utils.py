import json
import pandas as pd
import math

def json2df(data):

    #process json
    colnames = ['page','text','x1','y1','x2','y2','x3','y3','x4','y4']
    doc_txt = ""
    ln_txt = ""
    doc_df = pd.DataFrame(columns = colnames)

    #create a dataframe of text
    pg_cnt=0
    for pg in data['analyzeResult']['readResults']:
        
        df = pd.DataFrame(columns = colnames)
        for ln in pg['lines']:
            txt = ln['text']
            x1, y1, x2, y2, x3, y3, x4, y4 = ln['boundingBox']
            
            #correct for angle
            y1 = y1 - x1*math.tan(data['analyzeResult']['readResults'][0]['angle']* math.pi / 180)
            y2 = y2 - x2*math.tan(data['analyzeResult']['readResults'][0]['angle']* math.pi / 180)
            y3 = y3 - x3*math.tan(data['analyzeResult']['readResults'][0]['angle']* math.pi / 180)
            y4 = y4 - x4*math.tan(data['analyzeResult']['readResults'][0]['angle']* math.pi / 180)
            
            
            tdf = pd.DataFrame([[pg_cnt,txt,x1, y1, x2, y2, x3, y3, x4, y4]], columns = colnames)
            df = df.append(tdf, ignore_index=True)
            
        #identify line numbers
        df['txt_pos'] = (df['y1']+df['y2']+df['y3']+df['y4'])/4
        df['txt_ht'] = abs((df['y1']+df['y2']-df['y3']-df['y4'])/2)
        df['txt_pos_x'] = (df['x1']+df['x2']+df['x3']+df['x4'])/4
        
        df = df.sort_values(by = ['txt_pos'], ascending =True)
        df['line_gap'] = df['txt_pos'].diff()
        
        #correct for angle
        df['txt_gap_x'] = df['txt_pos_x'].diff()
        df['line_gap'] = df['line_gap'] - df['txt_gap_x']*math.tan(data['analyzeResult']['readResults'][0]['angle']* math.pi / 180)
        
        df['nxt_ln'] = df['line_gap'] > df['txt_ht']/2
        
        df['line_no'] = df['nxt_ln'].cumsum()
        df = df.sort_values(by = ['line_no','txt_pos_x'], ascending=True)

        #Merge text of same row
        df_text = df.groupby([df.page, df.line_no])['text'].apply(lambda x: ' '.join(x)).reset_index()

        df_x1 = df.groupby([df.page, df.line_no])['x1'].apply(min).reset_index()
        df_y1 = df.groupby([df.page, df.line_no])['y1'].apply(min).reset_index()
        df_x2 = df.groupby([df.page, df.line_no])['x2'].apply(max).reset_index()
        df_y2 = df.groupby([df.page, df.line_no])['y2'].apply(min).reset_index()
        df_x3 = df.groupby([df.page, df.line_no])['x3'].apply(max).reset_index()
        df_y3 = df.groupby([df.page, df.line_no])['y3'].apply(max).reset_index()
        df_x4 = df.groupby([df.page, df.line_no])['x4'].apply(min).reset_index()
        df_y4 = df.groupby([df.page, df.line_no])['y4'].apply(max).reset_index()

        df_page = pd.merge(df_text, df_x1)
        df_page = pd.merge(df_page, df_y1)
        df_page = pd.merge(df_page, df_x2)
        df_page = pd.merge(df_page, df_y2)
        df_page = pd.merge(df_page, df_x3)
        df_page = pd.merge(df_page, df_y3)
        df_page = pd.merge(df_page, df_x4)
        df_page = pd.merge(df_page, df_y4)

        #df_page = df  #remove this line
        doc_df = doc_df.append(df_page, ignore_index=True)
        pg_cnt = pg_cnt + 1

    return(doc_df)


from similarity.cosine import Cosine
##########################################################
# function to remove headers
##########################################################
def header(df, kgram=2, TOP_LINES=5):
    
    df['isHeader'] = False
    pgs = df['page'].unique()
    
    cosine = Cosine(kgram)
    for pg in pgs[1:]:
        
        prev_idx = df.index[df['page'] == (pg-1)]
        pres_idx = df.index[df['page'] == pg]
        
        for ln in range(TOP_LINES):
            
            s0 = df.loc[prev_idx[ln],'text']
            s1 = df.loc[pres_idx[ln],'text']
            
            skip=0
            if s0.isdigit():
                df.loc[prev_idx[ln], 'isHeader'] = True
                skip = 1
            
            if s1.isdigit():
                df.loc[pres_idx[ln], 'isHeader'] = True
                skip = 1
                
            if (skip == 1) | (len(s0) < kgram) | (len(s1) < kgram):
                continue;
            
            #print(s0,",", s1)
            p0 = cosine.get_profile(s0)
            p1 = cosine.get_profile(s1)
            
            sim = cosine.similarity_profiles(p0, p1)
            if(sim > 0.9):
                df.loc[prev_idx[ln], 'isHeader'] = True
                df.loc[pres_idx[ln], 'isHeader'] = True
                #print(pg,",", ln, ",", s0,",", s1,",", sim)        
        
    
    return(df)

##########################################################
# function to remove footers
##########################################################

def footer(df, kgram=2, TOP_LINES=5):
    
    df['isFooter'] = False
    pgs = df['page'].unique()
    
    cosine = Cosine(kgram)
    for pg in pgs[1:]:
        
        prev_idx = df.index[df['page'] == (pg-1)]
        pres_idx = df.index[df['page'] == pg]
        
        for ln in range(TOP_LINES):
            
            prev_ln = prev_idx[-1*(ln+1)]
            pres_ln = pres_idx[-1*(ln+1)]
            
            s0 = df.loc[prev_ln,'text']
            s1 = df.loc[pres_ln,'text']
            
            skip=0
            if s0.isdigit():
                df.loc[prev_ln, 'isFooter'] = True
                skip = 1
            
            if s1.isdigit():
                df.loc[pres_ln, 'isFooter'] = True
                skip = 1
                
            if (skip == 1) | (len(s0) < kgram) | (len(s1) < kgram):
                continue;
            
            #print(s0,",", s1)
            p0 = cosine.get_profile(s0)
            p1 = cosine.get_profile(s1)
            
            sim = cosine.similarity_profiles(p0, p1)
            if(sim > 0.9):
                df.loc[prev_ln, 'isFooter'] = True
                df.loc[pres_ln, 'isFooter'] = True
                #print(pg,",", ln, ",", s0,",", s1,",", sim)        
        
    
    return(df)
