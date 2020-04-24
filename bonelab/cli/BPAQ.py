# Imports
import argparse
import os
import time
import numpy as np
import pandas as pd

from bonelab.util.echo_arguments import echo_arguments

def message(msg, *additionalLines):
    """Print message with time stamp.
    
    The first argument is printed with a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    print(f'{(time.time()-start_time):8.2f} {msg}')
    for line in additionalLines:
        print(" " * 9 + line)
start_time = time.time()

# Table based on reverse-engineering the online BPAQ tool
def generate_table():
  d = {
    'Sport/Activity': ['ATHLETICS/TRACK','Jumps','Middle Distance','Throws','Sprints/Hurdles','Junior/Little athletics','BALL/STICK AND BALL SPORTS','Baseball','Cricket','Field Hockey','Golf (Walking)','Golf (electric car)','Ice hockey','Lacrosse','Softball','T-ball','BOWLING','Lawn bowling','Ten-pin bowling','CLIMBING','Rock/wall climbing','Gym based climbing','Bouldering','CYCLING','Recreational/transport purposes','Sprint','Endurance','DANCING','Ballet','Ballroom','Cheerleading','Contemporary','Highland','Hip Hop','Jazz','Line dancing/square dancing','Tap','FOOTBALL','Australian Rules Football','Flag football','Oz Tag','Rugby League','Rugby Union','Soccer','Touch Football','GYMNASTICS','Acrobatics','Gymnastics - Artistic','Gymnastics - Developmental','Gymnastics - Rhythmic','Trampolining','GYM/EXERCISE WORKOUT','Aerobics (high impact)','Aerobics (low impact)','Boot Camp','Cross-Fit','Eliptical trainer','High Intensity Personal Trainer','Pilates','Resistance training - Heavy upper and lower body','Resistance training - Heavy upper body','Resistance training - Heavy lower body','Resistance training - Light','Resistance training - Bodyweight (e.g. push ups/dips etc)','Skipping','Spin Class','Stairmaster','Treadmill - Running','Treadmill - Walking','Yoga','Zumba','HOUSEHOLD ACTIVITIES','Heavy indoor housework (lifting furniture/carry buckets etc)','Heavy gardening','JUMPING','Jump-rope/skipping','Plyometrics','LIFTING','Power Lifting','Resistance training - heavy','Resistance training - light','Body weight exercises (e.g. push ups/chin ups/dips etc)','MARTIAL ARTS','Aikido','Boxing','Hapkido','Judo','Karate','Kick boxing','Kung Fu','Tae Kwon Do','Tai Chi','Wrestling','OCCUPATIONAL ACTIVITY','Light-moderate occupational activity (e.g. on feet for at least 5 hours/day)','Heavy occupational work (e.g. landscaping/constructions/chopping etc)','RACQUET SPORT','Badminton','Ping pong/table tennis','Racquet ball','Squash','Tennis','RIDING','Horse Riding','Motor Cross','RUNNING/JOGGING','Beach sprint','Cross Country','Long distance/marathon','Middle distance','Recreational (jogging)','Sprint','SKATING','Ice hockey','Ice skating (recreational)','Figure skating/ice dancing','Roller blading','Roller derby','Roller skating','Scootering (active)','Skateboarding','SNOW SPORTS','Cross-country skiing/Biathlon','Snowshoeing','Skiing','Sledding/tobogganing','Snowboarding','SURFING','Kite surfing','Surfing (board) - recreational','Surfing (board) - competitive','Windsurfing','SWIMMING/POOL-BASED','Diving','Swimming (recreational/play)','Swimming (sprint/competitive)','Swimming (training/laps)','Scuba','Snorkeling','Synchronised swimming','Water aerobics','Water polo','THROWING & CATCHING SPORTS','Basketball','Beach volleyball','Handball (international)','Netball','Ultimate Frisbee','Volleyball','TRIATHALON','Junior/recreational triathlon','Competitive triathlon (incl. training)','WALKING','Hiking','Pedestrian/walking for leisure/walking to work or school','Mountaineering/orienteering','Power walking','Race walking','Stair climbing (i.e. for exercise/competition)','WATER SPORTS','Body boarding','Canoeing','Dragon boat','Kayaking','Kite surfing','Paddle board (standing)','Rowing','Sailing','Skulling','Surfing (board) - recreational','Surfing (board) - competitive','Wake boarding','Water skiing','Windsurfing','OTHER','Low impact (e.g. impact/intensity similar to walking)','Moderate impact (e.g. jumping/running/cutting)','High impact (e.g. near max aerobic intensity/max impact landing)'],
    'COEFF': ["",12.65,4.88,0.72,5.32,6.08,"",4.88,4.88,8.45,0.4,0.4,1.68,9.42,4.88,4.88,"",0.4,0.72,"",0.31,0.31,0.31,"",0.16,0.31,0.16,"",25.64,0.72,55,0.4,8.45,1.68,0.72,0.72,1.68,"",23.05,13.62,13.62,23.05,23.05,13.62,13.62,"",55,100,13.62,25.64,3,"",55,4.88,7.84,5.32,0.4,5.32,0.04,1.68,0.51,1.68,0.51,0.4,5.32,0.16,0.31,4.88,0.4,0.04,3,"",0.4,3,"",12.65,16.44,"",16.44,1.68,0.51,0.4,"",4.72,4.72,4.72,4.72,7.84,7.84,12.65,12.65,0.4,0.4,"",0.4,3,"",22.07,5.32,12.21,12.21,7.84,"",3,1.68,"",4.88,4.88,4.88,4.88,4.88,0.31,"",1.68,1.68,3,0.96,0.96,0.96,0.96,0.96,"",0.4,0.4,0.72,0.3,0.72,"",0.12,0.31,0.31,0.31,"",0.28,0.07,0.07,0.07,0.28,0.07,0.07,0.28,0.07,"",12.65,13.62,8.45,8.45,4.88,31.37,"",3,4.88,"",0.51,0.4,0.51,0.4,0.4,0.51,"",0.07,0.12,0.12,0.12,0.12,0.4,0.96,0.07,0.12,0.31,0.31,0.31,0.72,0.31,"",0.4,13.62,55],
    'redcap_base': ['bpaq_grp_ath','bpaq_ath_jump','bpaq_ath_mid','bpaq_ath_throw','bpaq_ath_hurd','bpaq_ath_junior','bpaq_grp_ball','bpaq_ball_baseball','bpaq_ball_cric','bpaq_ball_f_hoc','bpaq_ball_golf_walk','bpaq_ball_golf_car','bpaq_ball_ice_hoc','bpaq_ball_lacr','bpaq_ball_soft','bpaq_ball_tball','bpaq_grp_bowl','bpaq_lawn_bowl','bpaq_10pin','bpaq_grp_climb','bpaq_rock','bpaq_gym_climb','bpaq_boulder','bpaq_grp_cycle','bpaq_cycle_rec','bpaq_cycle_sprint','bpaq_cycle_end','bpaq_grp_dance','bpaq_ballet','bpaq_ballroom','bpaq_cheer','bpaq_cont','bpaq_high','bpaq_hiphop','bpaq_jazz','bpaq_line','bpaq_tap','bpaq_grp_football','bpaq_au_foot','bpaq_flag_foot','bpaq_oz_tag','bpaq_rugby','bpaq_rugby_un','bpaq_soccer','bpaq_foot','bpaq_grp_gymnastics','bpaq_acro','bpaq_art','bpaq_dev','bpaq_rhyt','bpaq_tramp','bpaq_grp_gym','bpaq_aero_high','bpaq_aero_low','bpaq_boot','bpaq_cross','bpaq_elip','bpaq_high_train','bpaq_pilates','bpaq_res_upp_low','bpaq_res_upp','bpaq_res_low','bpaq_res_light','bpaq_res_body','bpaq_skip','bpaq_spin','bpaq_stair','bpaq_tread_run','bpaq_tread_walk','bpaq_yoga','bpaq_zumba','bpaq_grp_house','bpaq_house','bpaq_gard','bpaq_grp_jump','bpaq_jumprope','bpaq_plyo','bpaq_grp_lifting','bpaq_power_lift','bpaq_res_heavy','bpaq_res_light1','bpaq_body_wt','bpaq_grp_ma','bpaq_aikido','bpaq_box','bpaq_hapk','bpaq_judo','bpaq_karate','bpaq_kick','bpaq_kungfu','bpaq_taekwondo','bpaq_taichi','bpaq_wrest','bpaq_grp_occ_act','bpaq_occ_light','bpaq_occ_heavy','bpaq_grp_rac_sport','bpaq_bad','bpaq_ping','bpaq_rac_ball','bpaq_squash','bpaq_tennis','bpaq_grp_riding','bpaq_horse','bpaq_motor','bpaq_grp_run','bpaq_beach_spr','bpaq_cross_count','bpaq_marat','bpaq_mid_dist','bpaq_jog','bpaq_sprint','bpaq_grp_skate','bpaq_hock','bpaq_ice_skate','bpaq_fig_skate','bpaq_roll_blade','bpaq_roll_derby','bpaq_roll_skate','bpaq_scoot','bpaq_skateboard','bpaq_grp_snow','bpaq_cross_ski','bpaq_snowshoe','bpaq_ski','bpaq_sled','bpaq_snowboard','bpaq_grp_surf','bpaq_kite_surf','bpaq_surf','bpaq_surf_comp','bpaq_windsurf','bpaq_grp_swim','bpaq_dive','bpaq_swim_rec','bpaq_swim_sprint','bpaq_swim_lap','bpaq_scuba','bpaq_snorkel','bpaq_syn_swim','bpaq_water_aerob','bpaq_water_polo','bpaq_grp_throw','bpaq_bball','bpaq_beachvol','bpaq_handball','bpaq_netball','bpaq_ult_fris','bpaq_volley','bpaq_grp_tri','bpaq_tri_rec','bpaq_tri_comp','bpaq_grp_walk','bpaq_hike','bpaq_walk','bpaq_mount','bpaq_pow_walk','bpaq_race_walk','bpaq_stair_cl','bpaq_grp_water_sport','bpaq_body_board','bpaq_canoe','bpaq_dragon','bpaq_kayak','bpaq_kite_surf1','bpaq_paddle','bpaq_row','bpaq_sail','bpaq_skull','bpaq_surf1','bpaq_surf_comp1','bpaq_wake','bpaq_water_ski','bpaq_windsurf1','bpaq_grp_other','bpaq_low_imp','bpaq_mod_imp','bpaq_high_imp'],
    'redcap_freq': ['bpaq_grp_ath','bpaq_jump_freq_wk','bpaq_mid_freq_wk','bpaq_throw_freq_wk','bpaq_hurd_freq_wk','bpaq_junior_freq_wk','bpaq_grp_ball','bpaq_baseball_freq_wk','bpaq_cric_freq_wk','bpaq_f_hoc_freq_wk','bpaq_golf_walk_freq_wk','bpaq_golf_car_freq_wk','bpaq_ice_hoc_freq_wk','bpaq_lacr_freq_wk','bpaq_soft_freq_wk','bpaq_tball_freq_wk','bpaq_grp_bowl','bpaq_lawn_bowl_freq_wk','bpaq_10pin_freq_wk','bpaq_grp_climb','bpaq_rock_freq_wk','bpaq_gym_climb_freq_wk','bpaq_boulder_freq_wk','bpaq_grp_cycle','bpaq_cycle_rec_freq_wk','bpaq_cycle_sprint_freq_wk','bpaq_cycle_end_freq_wk','bpaq_grp_dance','bpaq_ballet_freq_wk','bpaq_ballroom_freq_wk','bpaq_cheer_freq_wk','bpaq_cont_freq_wk','bpaq_high_freq_wk','bpaq_hiphop_freq_wk','bpaq_jazz_freq_wk','bpaq_line_freq_wk','bpaq_tap_freq_wk','bpaq_grp_football','bpaq_au_foot_freq_wk','bpaq_flag_foot_freq_wk','bpaq_oz_tag_freq_wk','bpaq_rugby_freq_wk','bpaq_rugby_un_freq_wk','bpaq_soccer_freq_wk','bpaq_foot_freq_wk','bpaq_grp_gymnastics','bpaq_acro_freq_wk','bpaq_art_freq_wk','bpaq_dev_freq_wk','bpaq_rhyt_freq_wk','bpaq_tramp_freq_wk','bpaq_grp_gym','bpaq_aero_high_freq_wk','bpaq_aero_low_freq_wk','bpaq_boot_freq_wk','bpaq_cross_freq_wk','bpaq_elip_freq_wk','bpaq_high_train_freq_wk','bpaq_pilates_freq_wk','bpaq_res_upp_low_freq_wk','bpaq_res_upp_freq_wk','bpaq_res_low_freq_wk','bpaq_res_light_freq_wk','bpaq_res_body_freq_wk','bpaq_skip_freq_wk','bpaq_spin_freq_wk','bpaq_stair_freq_wk','bpaq_tread_run_freq_wk','bpaq_tread_walk_freq_wk','bpaq_yoga_freq_wk','bpaq_zumba_freq_wk','bpaq_grp_house','bpaq_house_freq_wk','bpaq_gard_freq_wk','bpaq_grp_jump','bpaq_jumprope_freq_wk','bpaq_plyo_freq_wk','bpaq_grp_lifting','bpaq_power_lift_freq_wk','bpaq_res_heavy_freq_wk','bpaq_res_light1_freq_wk','bpaq_body_wt_freq_wk','bpaq_grp_ma','bpaq_aikido_freq_wk','bpaq_box_freq_wk','bpaq_hapk_freq_wk','bpaq_judo_freq_wk','bpaq_karate_freq_wk','bpaq_kick_freq_wk','bpaq_kungfu_freq_wk','bpaq_taekwondo_freq_wk','bpaq_taichi_freq_wk','bpaq_wrest_freq_wk','bpaq_grp_occ_act','bpaq_occ_light_freq_wk','bpaq_occ_heavy_freq_wk','bpaq_grp_rac_sport','bpaq_bad_freq_wk','bpaq_ping_freq_wk','bpaq_rac_ball_freq_wk','bpaq_squash_freq_wk','bpaq_tennis_freq_wk','bpaq_grp_riding','bpaq_horse_freq_wk','bpaq_motor_freq_wk','bpaq_grp_run','bpaq_beach_spr_freq_wk','bpaq_cross_count_freq_wk','bpaq_marat_freq_wk','bpaq_mid_dist_freq_wk','bpaq_jog_freq_wk','bpaq_sprint_freq_wk','bpaq_grp_skate','bpaq_hock_freq_wk','bpaq_ice_skate_freq_wk','bpaq_fig_skate_freq_wk','bpaq_roll_blade_freq_wk','bpaq_roll_derby_freq_wk','bpaq_roll_skate_freq_wk','bpaq_scoot_freq_wk','bpaq_skateboard_freq_wk','bpaq_grp_snow','bpaq_cross_ski_freq_wk','bpaq_snowshoe_freq_wk','bpaq_ski_freq_wk','bpaq_sled_freq_wk','bpaq_snowboard_freq_wk','bpaq_grp_surf','bpaq_kite_surf_freq_wk','bpaq_surf_freq_wk','bpaq_surf_comp_freq_wk','bpaq_windsurf_freq_wk','bpaq_grp_swim','bpaq_dive_freq_wk','bpaq_swim_rec_freq_wk','bpaq_swim_sprint_freq_wk','bpaq_swim_lap_freq_wk','bpaq_scuba_freq_wk','bpaq_snorkel_freq_wk','bpaq_syn_swim_freq_wk','bpaq_water_aerob_freq_wk','bpaq_water_polo_freq_wk','bpaq_grp_throw','bpaq_bball_freq_wk','bpaq_beachvol_freq_w','bpaq_handball_freq_wk','bpaq_netball_freq_wk','bpaq_ult_fris_freq_wk','bpaq_volley_freq_wk','bpaq_grp_tri','bpaq_tri_rec_freq_wk','bpaq_tri_comp_freq_wk','bpaq_grp_walk','bpaq_hike_freq_wk','bpaq_walk_freq_wk','bpaq_mount_freq_wk','bpaq_pow_walk_freq_wk','bpaq_race_walk_freq_wk','bpaq_stair_cl_freq_wk','bpaq_grp_water_sport','bpaq_body_board_freq_wk','bpaq_canoe_freq_wk','bpaq_dragon_freq_wk','bpaq_kayak_freq_wk','bpaq_kite_surf1_freq_wk','bpaq_paddle_freq_wk','bpaq_row_freq_wk','bpaq_sail_freq_wk','bpaq_skull_freq_wk','bpaq_surf1_freq_wk','bpaq_surf_comp1_freq_wk','bpaq_wake_freq_wk','bpaq_water_ski_freq_wk','bpaq_windsurf1_freq_wk','bpaq_grp_other','bpaq_low_imp_freq_wk','bpaq_mod_imp_freq_wk','bpaq_high_imp_freq_wk']
  }
  table = pd.DataFrame(data=d)
  table.set_index('redcap_base',inplace=True)
  return table

# Original Table6. Do not use this.
def generate_table6():
  d = {
    'Sport/Activity': ['Swimming','Rowing','Cycling','Diving (platform)','Scuba','Stairmaster','Windsurfing','Golf','Walking/Hiking','Shot put','Resistance training (lower limb)','Skiing','Waterskiing','Rollerblading','Skateboarding','Ice hockey','Horse-riding','Judo','Cricket','Running/Jogging','Track','Triathlon','Ultimate','Dance','Cross-country','Netball','Tennis','Lacrosse','Racquet ball','Squash','Kung Fu','Basketball','Jump Rope','T-ball','Baseball','Softball','Flag football','Rugby League/Union','Soccer','Touch football','Badminton','Australian Rules','Ballet','Ice skating (figure/dance)','Volleyball','Aerobics','Cheerleading','Gymnastics'],
    'Peak GRF': [0.7,1.0,0.8,1.0,1.0,1.1,1.1,1.2,1.2,1.2,1.8,1.2,1.2,1.2,1.2,1.2,1.5,2.1,2.6,2.6,2.6,2.6,2.6,2.7,2.9,2.9,4.7,3.5,2.6,2.6,4.7,4.7,4.7,2.9,2.9,2.9,2.9,2.9,2.9,2.9,4.7,4.7,4.7,4.8,5.5,5.5,5.5,10.0],
    'Rate': [2.5,3.0,5.0,7.0,7.1,7.1,7.1,8.4,8.4,8.4,7.1,15.0,15.0,20.0,20.0,35.0,50.0,56.2,46.9,46.9,46.9,46.9,46.9,49.3,56.2,56.2,41.7,67.3,117.4,117.4,67.3,67.3,67.3,117.4,117.4,117.4,117.4,117.4,117.4,117.4,117.4,122.6,136.4,136.4,142.6,250.0,250.0,250.0],
    'Effective load stimulus': [0.07,0.12,0.16,0.28,0.28,0.31,0.31,0.40,0.40,0.40,0.51,0.72,0.72,0.96,0.96,1.68,3.00,4.72,4.88,4.88,4.88,4.88,4.88,5.32,6.52,6.52,7.84,9.42,12.21,12.21,12.65,12.65,12.65,13.62,13.62,13.62,13.62,13.62,13.62,13.62,22.07,23.05,25.64,26.19,31.37,55.00,55.00,100.00]
  }
  table6 = pd.DataFrame(data=d)
  return table6

# Only useful when using the pd.head() function
def set_pandas_display_options() -> None:
    display = pd.options.display

    display.max_columns = 10
    display.max_rows = 200
    display.max_colwidth = 20
    # display.width = None
    # display.precision = 2
    
# Calculate how many different activites were reported
def calc_num_current_activities(freq_wk):
    if (freq_wk > 0):
        return 1
    return 0

# Calculate BPAQ score for activites within the last year
def calc_current_BPAQ(coeff,freq_wk,age):

    if (age<10):
        age_factor = 1.2
    elif (age<15):
        age_factor = 1.5
    elif (age<35):
        age_factor = 1.1
    else:
        age_factor = 1.0

    if not (isinstance(freq_wk,float) or isinstance(freq_wk,int)):
        print('WARNING: Variable freq_wk is neither float nor int.')
        print('         Variable freq_wk = ',freq_wk)
        print('         Setting freq_wk to 0')
        freq_wk = 0
        
    if (freq_wk>40): # max number of activities per week is 40
        freq_wk = 40

    if (freq_wk<1):
        return 0

    return ((coeff + 0.2*coeff*(freq_wk-1) ) * age_factor)
    
# Calculate BPAQ score for years of activity
def calc_past_BPAQ(coeff,years,age_factor):

    if not (isinstance(years,float) or isinstance(years,int)):
        print('WARNING: Variable years is neither float nor int.')
        print('         Variable years = ',years)
        print('         Setting years to 0')
        years = 0

    if (years>60): # max number of years is 60
        years = 60

    return (coeff * years * age_factor)

# Functions to generate activity variable names from a derivative
def current(base):
    return base

def past_child(base):
    if "bpaq_beachvol_freq_w" in base: # There is an error in REDCap
        base = "bpaq_beachvol_freq_wk"
    return base+"2"

def past_adult(base):
    if "bpaq_beachvol_freq_w" in base: # There is an error in REDCap
        base = "bpaq_beachvol_freq_wk"
    return base+"3"

def BPAQ(
    ifile,
    ofile,
    show_redcap=False,
    show_table=False):

    # Imports
    import argparse
    import os
    import time
    import numpy as np
    import pandas as pd

    set_pandas_display_options()

    # Get the coefficient table as a DataFrame
    df_table = generate_table()
    
    if (show_table):
        message("Show Table data.")
        print(df_table)
        exit()

    # Get the redcap variables as lists
    redcap_base = df_table.index.tolist()
    redcap_freq = df_table['redcap_freq'].tolist()
    
    # Remove all the variables indicating grouping
    for activity in redcap_base:
        if "_grp_" in activity:
            redcap_base.remove(activity)
    
    for activity in redcap_freq:
        if "_grp_" in activity:
            redcap_freq.remove(activity)
    
    if (show_redcap):
        message("Show REDCap variables.")
        for activity in redcap_base:
          print(activity)
        exit()
    
    # Read input data from an excel file
    message("Reading excel input file:\n"+ifile)

    df = pd.read_excel(ifile)
    df.set_index('record_id',inplace=True) # Assign the record ID as the table index
    df.fillna(0,inplace=True) # Fill NANs with zeros

    # Visual check
    #pd.options.display.max_columns = 10
    #pd.options.display.max_rows = 50
    #df.head(40)
    
    # Age must be included in the input data
    if 'age_enroll' not in df.columns:
        print('ERROR: Input data must include \'age_enroll\'')
        # print HELP
        exit()
    
    # Initiate and calculate scores
    message("Calculating BPAQ scores.")

    df['bpaq_current_activity'] = 0
    df['bpaq_current_num_activity'] = 0
    df['bpaq_curr_res'] = 0
    df['bpaq_past_child_activity'] = 0
    df['bpaq_past_adult_activity'] = 0
    df['bpaq_past_res'] = 0
    df['bpaq_tot_res'] = 0

    # Unfortunately, I couldn't see how to avoid a for-loop. This is SLOW....
    for activity in redcap_base:
    
        # Calculate the activity scores and number of activies so that
        # we can calculate the average current activity
        activity_coef = df_table.at[activity,'COEFF']
        activity_name = current(activity)
        activity_freq = current(df_table.at[activity,'redcap_freq'])
        df['bpaq_current_activity'] = df['bpaq_current_activity'] + \
                                      df.apply(lambda x:calc_current_BPAQ( \
                                               activity_coef, \
                                               x[activity_freq], \
                                               x['age_enroll']), \
                                               axis=1)

        df['bpaq_current_num_activity'] = df['bpaq_current_num_activity'] + \
                                          df.apply(lambda x:calc_num_current_activities( \
                                                   x[activity_freq]), \
                                                   axis=1)
        df['bpaq_curr_res'] = df.apply(lambda x: x['bpaq_current_num_activity'] \
                                                   if x['bpaq_current_num_activity']==0 else \
                                                   x['bpaq_current_activity']/x['bpaq_current_num_activity'], \
                                                   axis=1)
    
        # Calculate the past childhood activity
        age_factor = 0.25
        activity_coef = df_table.at[activity,'COEFF']
        activity_name = past_child(activity)
        activity_freq = past_child(df_table.at[activity,'redcap_freq'])
        df['bpaq_past_child_activity'] = df['bpaq_past_child_activity'] + \
                                         df.apply(lambda x:calc_past_BPAQ( \
                                                  activity_coef, \
                                                  x[activity_freq], \
                                                  age_factor), \
                                                  axis=1)

        # Calculate the past adulthood activity
        age_factor = 0.1
        activity_coef = df_table.at[activity,'COEFF']
        activity_name = past_adult(activity)
        activity_freq = past_adult(df_table.at[activity,'redcap_freq'])
        df['bpaq_past_adult_activity'] = df['bpaq_past_adult_activity'] + \
                                         df.apply(lambda x:calc_past_BPAQ( \
                                                  activity_coef, \
                                                  x[activity_freq], \
                                                  age_factor), \
                                                  axis=1)

    # Initiate and calculate final scores
    message("Finalizing BPAQ scores.")

    df['bpaq_past_res'] = 0
    df['bpaq_tot_res'] = 0
    df['bpaq_past_res'] = df.apply(lambda x: \
                                               x['bpaq_past_child_activity'] + \
                                               x['bpaq_past_adult_activity'], \
                                               axis=1)
    df['bpaq_tot_res'] = df.apply(lambda x: \
                                            (x['bpaq_past_res'] + \
                                            x['bpaq_curr_res'])/2.0, \
                                            axis=1)

    # Print output
    message("Writing output file:\n",ofile+'.csv')

    df[['redcap_event_name',\
        'bpaq_current_activity',\
        'bpaq_current_num_activity',\
        'bpaq_curr_res',\
        'bpaq_past_child_activity',\
        'bpaq_past_adult_activity',\
        'bpaq_past_res',\
        'bpaq_tot_res']].to_csv(ofile+'.csv', float_format='%.6g', index=True)  
    #df.to_excel(ofile+'.xlsx', index=True, sheet_name='BPAQ scores')  
    #df.head(15)

    exit()

def main():
    # Setup description
    description='''Compute bone-specific physical activity (BPAQ).

This software mimics the BPAQ online tool and allows large numbers of
subjects to be analyzed at the same time. Since we use REDCap for our
questionnaire data storage, this software is designed to take as input
the dump from REDCap and process it directly.

Although the approach in this sofware is based on the paper below, the
coefficients used to weigh the various activities are out of date. We
used the online tool to back-calculate the correct coefficients.

    Weeks BK, Beck BR (2008). The BPAQ: a bone-specific physical 
    activity assessment instrument. Osteoporos Int 19, 1567-1577.
    
-----------------------------------------------------------------------
The bone-specific physical activity (BPAQ) assessment instrument
is completed using a paper or REDCap delivery. The calculation 
is divided into three parts:

1. Current activites in the past 12 months
    BPAQ = [R + 0.2R(N-1)]*A
    where R is the coefficient, N is frequency per week (max 40),
    and A is an age weighting factor:
    A = 1.2 <10 yrs, 1.5 10-15 yrs, 1.1 15-35 yrs, 1.0 >35 yrs
    
2. Past childhood activities (0-15 yrs)
    BPAQ = R * Y * A
    where R is the coefficient, Y is years of participation (max
    15), and A is an age weighting factor:
    A = 0.25 <15 yrs
    
3. Past adulthood activities (>15yrs)
    BPAQ = R * Y * A
    where coefficients are the same above except the max number
    years of participation is capped at 60. Age weighting factor:
    A = 0.10 >15 yrs

The input from REDCap includes too many variables to explain. To
see a summary of the coefficients for each activity, see the
HELP menu for an option to display. The variable names are organized
so that each one is unique. 

-----------------------------------------------------------------------

There are *groups* of types of 
activity (e.g. `bpaq_grp_ath` is the group for athletics), and
for each group each activity is listed. If a participated in
an activity, it is recorded as a 1 or 0 (e.g. `bpaq_ath_jump`),
and then frequency of activity (e.g. `bpaq_jump_freq_wk`).

There are three sets of variables representing current, past
childhood and past adulthood. For example, these would be
`bpaq_jump_freq_wk, bpaq_jump_freq_wk2, bpaq_jump_freq_wk3` and
`bpaq_ath_jump, bpaq_ath_jump2, bpaq_ath_jump3`.

Although the name of the variable may include `_freq_wk`, it 
represents 'times per week' if a current activity, or 'number
of years' if a past childhood or adult activity.

-----------------------------------------------------------------------

Example usage:

    blBPAQ ~/Desktop/BPAQ/tmp.xlsx -o output.txt
    blBPAQ ~/Desktop/BPAQ/bpaq_data_labels.xlsx -o output.txt
    blBPAQ NORMXT2_bpaq.txt -o output.txt

    blBPAQ /Users/skboyd/Desktop/BPAQ/bpaq_data_labels_nohead_mini.xlsx -o /Users/skboyd/Desktop/BPAQ/bpaq_out -t -r

The output is designed for easy upload to a data archive system 
such as REDCap. 

Hints and tips:

1. You MUST include 'age_enroll' in the REDCap input.

2. If you run into problems, try using an Excel sheet with only 30 or
   40 subject data (rows)

3. Sometimes the format of cells can cause a problem (i.e. an integer being
   expressed as a date). Select all the cells and choose a 'number' format.
   
Installation requirements include pandas and xlrd.

Steven Boyd, April 24, 2020.

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blExtractFields",
        description=description
    )
    parser.add_argument('ifile', help='Input Excel file of completed BPAQ instrument')
    parser.add_argument('-o','--ofile',help='Output BPAQ scores')
    parser.add_argument('-t','--show_table',action="store_true",
                        help='Show coefficients (was Table 6) (default: %(default)s)')
    parser.add_argument('-r','--show_redcap',action="store_true",
                        help='Show REDCap variables (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('BPAQ', vars(args)))

    # Run program
    BPAQ(**vars(args))

if __name__ == '__main__':
    main()
