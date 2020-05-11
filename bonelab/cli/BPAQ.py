# Imports
import argparse
import os
import time
import csv
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

# Prints a template for completing an individual profile
# It's very ugly how I've made this long, but otherwise
# it takes up too many lines. 
def print_profile_template(fn):
    f = open(fn, "w")
    print("Parameter,                                                                           Sport/Activity,            past_year, before_15yrs,  after_15yrs", file=f),print("redcap,                                                                                       units,            [per_wk],    [num_yrs],    [num_yrs]", file=f),print("record_id,                                                                                     name,            JOHN_DOE,,", file=f),print("age_enroll,                                                                                   years,            0,,", file=f),print("bpaq_grp_ath,                                                                       ATHLETICS/TRACK,,,", file=f),print("bpaq_ath_jump,                                                                                Jumps,            0,            0,            0", file=f),print("bpaq_ath_mid,                                                                       Middle Distance,            0,            0,            0", file=f),print("bpaq_ath_throw,                                                                              Throws,            0,            0,            0", file=f),print("bpaq_ath_hurd,                                                                      Sprints/Hurdles,            0,            0,            0", file=f),print("bpaq_ath_junior,                                                            Junior/Little athletics,            0,            0,            0", file=f),print("bpaq_grp_ball,                                                           BALL/STICK AND BALL SPORTS,,,", file=f),print("bpaq_ball_baseball,                                                                        Baseball,            0,            0,            0", file=f),print("bpaq_ball_cric,                                                                             Cricket,            0,            0,            0", file=f),print("bpaq_ball_f_hoc,                                                                       Field Hockey,            0,            0,            0", file=f),print("bpaq_ball_golf_walk,                                                                 Golf (Walking),            0,            0,            0", file=f),print("bpaq_ball_golf_car,                                                             Golf (electric car),            0,            0,            0", file=f),print("bpaq_ball_ice_hoc,                                                                       Ice hockey,            0,            0,            0", file=f),print("bpaq_ball_lacr,                                                                            Lacrosse,            0,            0,            0", file=f),print("bpaq_ball_soft,                                                                            Softball,            0,            0,            0", file=f),print("bpaq_ball_tball,                                                                             T-ball,            0,            0,            0", file=f),print("bpaq_grp_bowl,                                                                              BOWLING,,,", file=f),print("bpaq_lawn_bowl,                                                                        Lawn bowling,            0,            0,            0", file=f),print("bpaq_10pin,                                                                         Ten-pin bowling,            0,            0,            0", file=f),print("bpaq_grp_climb,                                                                            CLIMBING,,,", file=f),print("bpaq_rock,                                                                       Rock/wall climbing,            0,            0,            0", file=f),print("bpaq_gym_climb,                                                                  Gym based climbing,            0,            0,            0", file=f),print("bpaq_boulder,                                                                            Bouldering,            0,            0,            0", file=f),print("bpaq_grp_cycle,                                                                             CYCLING,,,", file=f),print("bpaq_cycle_rec,                                                     Recreational/transport purposes,            0,            0,            0", file=f),print("bpaq_cycle_sprint,                                                                           Sprint,            0,            0,            0", file=f),print("bpaq_cycle_end,                                                                           Endurance,            0,            0,            0", file=f),print("bpaq_grp_dance,                                                                             DANCING,,,", file=f),print("bpaq_ballet,                                                                                 Ballet,            0,            0,            0", file=f),print("bpaq_ballroom,                                                                             Ballroom,            0,            0,            0", file=f),print("bpaq_cheer,                                                                            Cheerleading,            0,            0,            0", file=f),print("bpaq_cont,                                                                             Contemporary,            0,            0,            0", file=f),print("bpaq_high,                                                                                 Highland,            0,            0,            0", file=f),print("bpaq_hiphop,                                                                                Hip Hop,            0,            0,            0", file=f),print("bpaq_jazz,                                                                                     Jazz,            0,            0,            0", file=f),print("bpaq_line,                                                              Line dancing/square dancing,            0,            0,            0", file=f),print("bpaq_tap,                                                                                       Tap,            0,            0,            0", file=f),print("bpaq_grp_football,                                                                         FOOTBALL,,,", file=f),print("bpaq_au_foot,                                                             Australian Rules Football,            0,            0,            0", file=f),print("bpaq_flag_foot,                                                                       Flag football,            0,            0,            0", file=f),print("bpaq_oz_tag,                                                                                 Oz Tag,            0,            0,            0", file=f),print("bpaq_rugby,                                                                            Rugby League,            0,            0,            0", file=f),print("bpaq_rugby_un,                                                                          Rugby Union,            0,            0,            0", file=f),print("bpaq_soccer,                                                                                 Soccer,            0,            0,            0", file=f),print("bpaq_foot,                                                                           Touch Football,            0,            0,            0", file=f),print("bpaq_grp_gymnastics,                                                                     GYMNASTICS,,,", file=f),print("bpaq_acro,                                                                               Acrobatics,            0,            0,            0", file=f),print("bpaq_art,                                                                     Gymnastics - Artistic,            0,            0,            0", file=f),print("bpaq_dev,                                                                Gymnastics - Developmental,            0,            0,            0", file=f),print("bpaq_rhyt,                                                                    Gymnastics - Rhythmic,            0,            0,            0", file=f),print("bpaq_tramp,                                                                            Trampolining,            0,            0,            0", file=f),print("bpaq_grp_gym,                                                                  GYM/EXERCISE WORKOUT,,,", file=f),print("bpaq_aero_high,                                                              Aerobics (high impact),            0,            0,            0", file=f),print("bpaq_aero_low,                                                                Aerobics (low impact),            0,            0,            0", file=f),print("bpaq_boot,                                                                                Boot Camp,            0,            0,            0", file=f),print("bpaq_cross,                                                                               Cross-Fit,            0,            0,            0", file=f),print("bpaq_elip,                                                                        Eliptical trainer,            0,            0,            0", file=f),print("bpaq_high_train,                                                    High Intensity Personal Trainer,            0,            0,            0", file=f),print("bpaq_pilates,                                                                               Pilates,            0,            0,            0", file=f),print("bpaq_res_upp_low,                                  Resistance training - Heavy upper and lower body,            0,            0,            0", file=f),print("bpaq_res_upp,                                                Resistance training - Heavy upper body,            0,            0,            0", file=f),print("bpaq_res_low,                                                Resistance training - Heavy lower body,            0,            0,            0", file=f),print("bpaq_res_light,                                                         Resistance training - Light,            0,            0,            0", file=f),print("bpaq_res_body,                            Resistance training - Bodyweight (e.g. push ups/dips etc),            0,            0,            0", file=f),print("bpaq_skip,                                                                                 Skipping,            0,            0,            0", file=f),print("bpaq_spin,                                                                               Spin Class,            0,            0,            0", file=f),print("bpaq_stair,                                                                             Stairmaster,            0,            0,            0", file=f),print("bpaq_tread_run,                                                                 Treadmill - Running,            0,            0,            0", file=f),print("bpaq_tread_walk,                                                                Treadmill - Walking,            0,            0,            0", file=f),print("bpaq_yoga,                                                                                     Yoga,            0,            0,            0", file=f),print("bpaq_zumba,                                                                                   Zumba,            0,            0,            0", file=f),print("bpaq_grp_house,                                                                HOUSEHOLD ACTIVITIES,,,", file=f),print("bpaq_house,                            Heavy indoor housework (lifting furniture/carry buckets etc),            0,            0,            0", file=f),print("bpaq_gard,                                                                          Heavy gardening,            0,            0,            0", file=f),print("bpaq_grp_jump,                                                                              JUMPING,,,", file=f),print("bpaq_jumprope,                                                                   Jump-rope/skipping,            0,            0,            0", file=f),print("bpaq_plyo,                                                                              Plyometrics,            0,            0,            0", file=f),print("bpaq_grp_lifting,                                                                           LIFTING,,,", file=f),print("bpaq_power_lift,                                                                      Power Lifting,            0,            0,            0", file=f),print("bpaq_res_heavy,                                                         Resistance training - heavy,            0,            0,            0", file=f),print("bpaq_res_light1,                                                        Resistance training - light,            0,            0,            0", file=f),print("bpaq_body_wt,                               Body weight exercises (e.g. push ups/chin ups/dips etc),            0,            0,            0", file=f),print("bpaq_grp_ma,                                                                           MARTIAL ARTS,,,", file=f),print("bpaq_aikido,                                                                                 Aikido,            0,            0,            0", file=f),print("bpaq_box,                                                                                    Boxing,            0,            0,            0", file=f),print("bpaq_hapk,                                                                                  Hapkido,            0,            0,            0", file=f),print("bpaq_judo,                                                                                     Judo,            0,            0,            0", file=f),print("bpaq_karate,                                                                                 Karate,            0,            0,            0", file=f),print("bpaq_kick,                                                                              Kick boxing,            0,            0,            0", file=f),print("bpaq_kungfu,                                                                                Kung Fu,            0,            0,            0", file=f),print("bpaq_taekwondo,                                                                         Tae Kwon Do,            0,            0,            0", file=f),print("bpaq_taichi,                                                                                Tai Chi,            0,            0,            0", file=f),print("bpaq_wrest,                                                                               Wrestling,            0,            0,            0", file=f),print("bpaq_grp_occ_act,                                                             OCCUPATIONAL ACTIVITY,,,", file=f),print("bpaq_occ_light,        Light-moderate occupational activity (e.g. on feet for at least 5 hours/day),            0,            0,            0", file=f),print("bpaq_occ_heavy,               Heavy occupational work (e.g. landscaping/constructions/chopping etc),            0,            0,            0", file=f),print("bpaq_grp_rac_sport,                                                                   RACQUET SPORT,,,", file=f),print("bpaq_bad,                                                                                 Badminton,            0,            0,            0", file=f),print("bpaq_ping,                                                                   Ping pong/table tennis,            0,            0,            0", file=f),print("bpaq_rac_ball,                                                                         Racquet ball,            0,            0,            0", file=f),print("bpaq_squash,                                                                                 Squash,            0,            0,            0", file=f),print("bpaq_tennis,                                                                                 Tennis,            0,            0,            0", file=f),print("bpaq_grp_riding,                                                                             RIDING,,,", file=f),print("bpaq_horse,                                                                            Horse Riding,            0,            0,            0", file=f),print("bpaq_motor,                                                                             Motor Cross,            0,            0,            0", file=f),print("bpaq_grp_run,                                                                       RUNNING/JOGGING,,,", file=f),print("bpaq_beach_spr,                                                                        Beach sprint,            0,            0,            0", file=f),print("bpaq_cross_count,                                                                     Cross Country,            0,            0,            0", file=f),print("bpaq_marat,                                                                  Long distance/marathon,            0,            0,            0", file=f),print("bpaq_mid_dist,                                                                      Middle distance,            0,            0,            0", file=f),print("bpaq_jog,                                                               RecreRecreational (jogging),            0,            0,            0", file=f),print("bpaq_sprint,                                                                                 Sprint,            0,            0,            0", file=f),print("bpaq_grp_skate,                                                                             SKATING,,,", file=f),print("bpaq_hock,                                                                               Ice hockey,            0,            0,            0", file=f),print("bpaq_ice_skate,                                                          Ice skating (recreational),            0,            0,            0", file=f),print("bpaq_fig_skate,                                                          Figure skating/ice dancing,            0,            0,            0", file=f),print("bpaq_roll_blade,                                                                     Roller blading,            0,            0,            0", file=f),print("bpaq_roll_derby,                                                                       Roller derby,            0,            0,            0", file=f),print("bpaq_roll_skate,                                                                     Roller skating,            0,            0,            0", file=f),print("bpaq_scoot,                                                                     Scootering (active),            0,            0,            0", file=f),print("bpaq_skateboard,                                                                      Skateboarding,            0,            0,            0", file=f),print("bpaq_grp_snow,                                                                          SNOW SPORTS,,,", file=f),print("bpaq_cross_ski,                                                       Cross-country skiing/Biathlon,            0,            0,            0", file=f),print("bpaq_snowshoe,                                                                          Snowshoeing,            0,            0,            0", file=f),print("bpaq_ski,                                                                                    Skiing,            0,            0,            0", file=f),print("bpaq_sled,                                                                     Sledding/tobogganing,            0,            0,            0", file=f),print("bpaq_snowboard,                                                                        Snowboarding,            0,            0,            0", file=f),print("bpaq_grp_surf,                                                                              SURFING,,,", file=f),print("bpaq_kite_surf,                                                                        Kite surfing,            0,            0,            0", file=f),print("bpaq_surf,                                                           Surfing (board) - recreational,            0,            0,            0", file=f),print("bpaq_surf_comp,                                                       Surfing (board) - competitive,            0,            0,            0", file=f),print("bpaq_windsurf,                                                                          Windsurfing,            0,            0,            0", file=f),print("bpaq_grp_swim,                                                                  SWIMMING/POOL-BASED,,,", file=f),print("bpaq_dive,                                                                                   Diving,            0,            0,            0", file=f),print("bpaq_swim_rec,                                                         Swimming (recreational/play),            0,            0,            0", file=f),print("bpaq_swim_sprint,                                                     Swimming (sprint/competitive),            0,            0,            0", file=f),print("bpaq_swim_lap,                                                             Swimming (training/laps),            0,            0,            0", file=f),print("bpaq_scuba,                                                                                   Scuba,            0,            0,            0", file=f),print("bpaq_snorkel,                                                                            Snorkeling,            0,            0,            0", file=f),print("bpaq_syn_swim,                                                                Synchronised swimming,            0,            0,            0", file=f),print("bpaq_water_aerob,                                                                    Water aerobics,            0,            0,            0", file=f),print("bpaq_water_polo,                                                                         Water polo,            0,            0,            0", file=f),print("bpaq_grp_throw,                                                          THROWING & CATCHING SPORTS,,,", file=f),print("bpaq_bball,                                                                              Basketball,            0,            0,            0", file=f),print("bpaq_beachvol,                                                                     Beach volleyball,            0,            0,            0", file=f),print("bpaq_handball,                                                             Handball (international),            0,            0,            0", file=f),print("bpaq_netball,                                                                               Netball,            0,            0,            0", file=f),print("bpaq_ult_fris,                                                                     Ultimate Frisbee,            0,            0,            0", file=f),print("bpaq_volley,                                                                             Volleyball,            0,            0,            0", file=f),print("bpaq_grp_tri,                                                                            TRIATHALON,,,", file=f),print("bpaq_tri_rec,                                                         Junior/recreational triathlon,            0,            0,            0", file=f),print("bpaq_tri_comp,                                               Competitive triathlon (incl. training),            0,            0,            0", file=f),print("bpaq_grp_walk,                                                                              WALKING,,,", file=f),print("bpaq_hike,                                                                                   Hiking,            0,            0,            0", file=f),print("bpaq_walk,                                 Pedestrian/walking for leisure/walking to work or school,            0,            0,            0", file=f),print("bpaq_mount,                                                             Mountaineering/orienteering,            0,            0,            0", file=f),print("bpaq_pow_walk,                                                                        Power walking,            0,            0,            0", file=f),print("bpaq_race_walk,                                                                        Race walking,            0,            0,            0", file=f),print("bpaq_stair_cl,                                       Stair climbing (i.e. for exercise/competition),            0,            0,            0", file=f),print("bpaq_grp_water_sport,                                                                  WATER SPORTS,,,", file=f),print("bpaq_body_board,                                                                      Body boarding,            0,            0,            0", file=f),print("bpaq_canoe,                                                                                Canoeing,            0,            0,            0", file=f),print("bpaq_dragon,                                                                            Dragon boat,            0,            0,            0", file=f),print("bpaq_kayak,                                                                                Kayaking,            0,            0,            0", file=f),print("bpaq_kite_surf1,                                                                       Kite surfing,            0,            0,            0", file=f),print("bpaq_paddle,                                                                Paddle board (standing),            0,            0,            0", file=f),print("bpaq_row,                                                                                    Rowing,            0,            0,            0", file=f),print("bpaq_sail,                                                                                  Sailing,            0,            0,            0", file=f),print("bpaq_skull,                                                                                Skulling,            0,            0,            0", file=f),print("bpaq_surf1,                                                          Surfing (board) - recreational,            0,            0,            0", file=f),print("bpaq_surf_comp1,                                                      Surfing (board) - competitive,            0,            0,            0", file=f),print("bpaq_wake,                                                                            Wake boarding,            0,            0,            0", file=f),print("bpaq_water_ski,                                                                        Water skiing,            0,            0,            0", file=f),print("bpaq_windsurf1,                                                                         Windsurfing,            0,            0,            0", file=f),print("bpaq_grp_other,                                                                               OTHER,,,", file=f),print("bpaq_low_imp,                                 Low impact (e.g. impact/intensity similar to walking),            0,            0,            0", file=f),print("bpaq_mod_imp,                                        Moderate impact (e.g. jumping/running/cutting),            0,            0,            0", file=f),print("bpaq_high_imp,                     High impact (e.g. near max aerobic intensity/max impact landing),            0,            0,            0", file=f)
    f.close()
    return

def setup_redcap_dictionary():
  myDict = {
    'bpaq_ath_jump':	['bpaq_jump_freq_wk',	'bpaq_jump_freq_wk2',	'bpaq_jump_freq_wk3'],
    'bpaq_ath_mid':	['bpaq_mid_freq_wk',	'bpaq_mid_freq_wk2',	'bpaq_mid_freq_wk3'],
    'bpaq_ath_throw':	['bpaq_throw_freq_wk',	'bpaq_throw_freq_wk2',	'bpaq_throw_freq_wk3'],
    'bpaq_ath_hurd':	['bpaq_hurd_freq_wk',	'bpaq_hurd_freq_wk2',	'bpaq_hurd_freq_wk3'],
    'bpaq_ath_junior':	['bpaq_junior_freq_wk',	'bpaq_junior_freq_wk2',	'bpaq_junior_freq_wk3'],
    'bpaq_ball_baseball':	['bpaq_baseball_freq_wk',	'bpaq_baseball_freq_wk2',	'bpaq_baseball_freq_wk3'],
    'bpaq_ball_cric':	['bpaq_cric_freq_wk',	'bpaq_cric_freq_wk2',	'bpaq_cric_freq_wk3'],
    'bpaq_ball_f_hoc':	['bpaq_f_hoc_freq_wk',	'bpaq_f_hoc_freq_wk2',	'bpaq_f_hoc_freq_wk3'],
    'bpaq_ball_golf_walk':	['bpaq_golf_walk_freq_wk',	'bpaq_golf_walk_freq_wk2',	'bpaq_golf_walk_freq_wk3'],
    'bpaq_ball_golf_car':	['bpaq_golf_car_freq_wk',	'bpaq_golf_car_freq_wk2',	'bpaq_golf_car_freq_wk3'],
    'bpaq_ball_ice_hoc':	['bpaq_ice_hoc_freq_wk',	'bpaq_ice_hoc_freq_wk2',	'bpaq_ice_hoc_freq_wk3'],
    'bpaq_ball_lacr':	['bpaq_lacr_freq_wk',	'bpaq_lacr_freq_wk2',	'bpaq_lacr_freq_wk3'],
    'bpaq_ball_soft':	['bpaq_soft_freq_wk',	'bpaq_soft_freq_wk2',	'bpaq_soft_freq_wk3'],
    'bpaq_ball_tball':	['bpaq_tball_freq_wk',	'bpaq_tball_freq_wk2',	'bpaq_tball_freq_wk3'],
    'bpaq_lawn_bowl':	['bpaq_lawn_bowl_freq_wk',	'bpaq_lawn_bowl_freq_wk2',	'bpaq_lawn_bowl_freq_wk3'],
    'bpaq_10pin':	['bpaq_10pin_freq_wk',	'bpaq_10pin_freq_wk2',	'bpaq_10pin_freq_wk3'],
    'bpaq_rock':	['bpaq_rock_freq_wk',	'bpaq_rock_freq_wk2',	'bpaq_rock_freq_wk3'],
    'bpaq_gym_climb':	['bpaq_gym_climb_freq_wk',	'bpaq_gym_climb_freq_wk2',	'bpaq_gym_climb_freq_wk3'],
    'bpaq_boulder':	['bpaq_boulder_freq_wk',	'bpaq_boulder_freq_wk2',	'bpaq_boulder_freq_wk3'],
    'bpaq_cycle_rec':	['bpaq_cycle_rec_freq_wk',	'bpaq_cycle_rec_freq_wk2',	'bpaq_cycle_rec_freq_wk3'],
    'bpaq_cycle_sprint':	['bpaq_cycle_sprint_freq_wk',	'bpaq_cycle_sprint_freq_wk2',	'bpaq_cycle_sprint_freq_wk3'],
    'bpaq_cycle_end':	['bpaq_cycle_end_freq_wk',	'bpaq_cycle_end_freq_wk2',	'bpaq_cycle_end_freq_wk3'],
    'bpaq_ballet':	['bpaq_ballet_freq_wk',	'bpaq_ballet_freq_wk2',	'bpaq_ballet_freq_wk3'],
    'bpaq_ballroom':	['bpaq_ballroom_freq_wk',	'bpaq_ballroom_freq_wk2',	'bpaq_ballroom_freq_wk3'],
    'bpaq_cheer':	['bpaq_cheer_freq_wk',	'bpaq_cheer_freq_wk2',	'bpaq_cheer_freq_wk3'],
    'bpaq_cont':	['bpaq_cont_freq_wk',	'bpaq_cont_freq_wk2',	'bpaq_cont_freq_wk3'],
    'bpaq_high':	['bpaq_high_freq_wk',	'bpaq_high_freq_wk2',	'bpaq_high_freq_wk3'],
    'bpaq_hiphop':	['bpaq_hiphop_freq_wk',	'bpaq_hiphop_freq_wk2',	'bpaq_hiphop_freq_wk3'],
    'bpaq_jazz':	['bpaq_jazz_freq_wk',	'bpaq_jazz_freq_wk2',	'bpaq_jazz_freq_wk3'],
    'bpaq_line':	['bpaq_line_freq_wk',	'bpaq_line_freq_wk2',	'bpaq_line_freq_wk3'],
    'bpaq_tap':	['bpaq_tap_freq_wk',	'bpaq_tap_freq_wk2',	'bpaq_tap_freq_wk3'],
    'bpaq_au_foot':	['bpaq_au_foot_freq_wk',	'bpaq_au_foot_freq_wk2',	'bpaq_au_foot_freq_wk3'],
    'bpaq_flag_foot':	['bpaq_flag_foot_freq_wk',	'bpaq_flag_foot_freq_wk2',	'bpaq_flag_foot_freq_wk3'],
    'bpaq_oz_tag':	['bpaq_oz_tag_freq_wk',	'bpaq_oz_tag_freq_wk2',	'bpaq_oz_tag_freq_wk3'],
    'bpaq_rugby':	['bpaq_rugby_freq_wk',	'bpaq_rugby_freq_wk2',	'bpaq_rugby_freq_wk3'],
    'bpaq_rugby_un':	['bpaq_rugby_un_freq_wk',	'bpaq_rugby_un_freq_wk2',	'bpaq_rugby_un_freq_wk3'],
    'bpaq_soccer':	['bpaq_soccer_freq_wk',	'bpaq_soccer_freq_wk2',	'bpaq_soccer_freq_wk3'],
    'bpaq_foot':	['bpaq_foot_freq_wk',	'bpaq_foot_freq_wk2',	'bpaq_foot_freq_wk3'],
    'bpaq_acro':	['bpaq_acro_freq_wk',	'bpaq_acro_freq_wk2',	'bpaq_acro_freq_wk3'],
    'bpaq_art':	['bpaq_art_freq_wk',	'bpaq_art_freq_wk2',	'bpaq_art_freq_wk3'],
    'bpaq_dev':	['bpaq_dev_freq_wk',	'bpaq_dev_freq_wk2',	'bpaq_dev_freq_wk3'],
    'bpaq_rhyt':	['bpaq_rhyt_freq_wk',	'bpaq_rhyt_freq_wk2',	'bpaq_rhyt_freq_wk3'],
    'bpaq_tramp':	['bpaq_tramp_freq_wk',	'bpaq_tramp_freq_wk2',	'bpaq_tramp_freq_wk3'],
    'bpaq_aero_high':	['bpaq_aero_high_freq_wk',	'bpaq_aero_high_freq_wk2',	'bpaq_aero_high_freq_wk3'],
    'bpaq_aero_low':	['bpaq_aero_low_freq_wk',	'bpaq_aero_low_freq_wk2',	'bpaq_aero_low_freq_wk3'],
    'bpaq_boot':	['bpaq_boot_freq_wk',	'bpaq_boot_freq_wk2',	'bpaq_boot_freq_wk3'],
    'bpaq_cross':	['bpaq_cross_freq_wk',	'bpaq_cross_freq_wk2',	'bpaq_cross_freq_wk3'],
    'bpaq_elip':	['bpaq_elip_freq_wk',	'bpaq_elip_freq_wk2',	'bpaq_elip_freq_wk3'],
    'bpaq_high_train':	['bpaq_high_train_freq_wk',	'bpaq_high_train_freq_wk2',	'bpaq_high_train_freq_wk3'],
    'bpaq_pilates':	['bpaq_pilates_freq_wk',	'bpaq_pilates_freq_wk2',	'bpaq_pilates_freq_wk3'],
    'bpaq_res_upp_low':	['bpaq_res_upp_low_freq_wk',	'bpaq_res_upp_low_freq_wk2',	'bpaq_res_upp_low_freq_wk3'],
    'bpaq_res_upp':	['bpaq_res_upp_freq_wk',	'bpaq_res_upp_freq_wk2',	'bpaq_res_upp_freq_wk3'],
    'bpaq_res_low':	['bpaq_res_low_freq_wk',	'bpaq_res_low_freq_wk2',	'bpaq_res_low_freq_wk3'],
    'bpaq_res_light':	['bpaq_res_light_freq_wk',	'bpaq_res_light_freq_wk2',	'bpaq_res_light_freq_wk3'],
    'bpaq_res_body':	['bpaq_res_body_freq_wk',	'bpaq_res_body_freq_wk2',	'bpaq_res_body_freq_wk3'],
    'bpaq_skip':	['bpaq_skip_freq_wk',	'bpaq_skip_freq_wk2',	'bpaq_skip_freq_wk3'],
    'bpaq_spin':	['bpaq_spin_freq_wk',	'bpaq_spin_freq_wk2',	'bpaq_spin_freq_wk3'],
    'bpaq_stair':	['bpaq_stair_freq_wk',	'bpaq_stair_freq_wk2',	'bpaq_stair_freq_wk3'],
    'bpaq_tread_run':	['bpaq_tread_run_freq_wk',	'bpaq_tread_run_freq_wk2',	'bpaq_tread_run_freq_wk3'],
    'bpaq_tread_walk':	['bpaq_tread_walk_freq_wk',	'bpaq_tread_walk_freq_wk2',	'bpaq_tread_walk_freq_wk3'],
    'bpaq_yoga':	['bpaq_yoga_freq_wk',	'bpaq_yoga_freq_wk2',	'bpaq_yoga_freq_wk3'],
    'bpaq_zumba':	['bpaq_zumba_freq_wk',	'bpaq_zumba_freq_wk2',	'bpaq_zumba_freq_wk3'],
    'bpaq_house':	['bpaq_house_freq_wk',	'bpaq_house_freq_wk2',	'bpaq_house_freq_wk3'],
    'bpaq_gard':	['bpaq_gard_freq_wk',	'bpaq_gard_freq_wk2',	'bpaq_gard_freq_wk3'],
    'bpaq_jumprope':	['bpaq_jumprope_freq_wk',	'bpaq_jumprope_freq_wk2',	'bpaq_jumprope_freq_wk3'],
    'bpaq_plyo':	['bpaq_plyo_freq_wk',	'bpaq_plyo_freq_wk2',	'bpaq_plyo_freq_wk3'],
    'bpaq_power_lift':	['bpaq_power_lift_freq_wk',	'bpaq_power_lift_freq_wk2',	'bpaq_power_lift_freq_wk3'],
    'bpaq_res_heavy':	['bpaq_res_heavy_freq_wk',	'bpaq_res_heavy_freq_wk2',	'bpaq_res_heavy_freq_wk3'],
    'bpaq_res_light1':	['bpaq_res_light1_freq_wk',	'bpaq_res_light1_freq_wk2',	'bpaq_res_light1_freq_wk3'],
    'bpaq_body_wt':	['bpaq_body_wt_freq_wk',	'bpaq_body_wt_freq_wk2',	'bpaq_body_wt_freq_wk3'],
    'bpaq_aikido':	['bpaq_aikido_freq_wk',	'bpaq_aikido_freq_wk2',	'bpaq_aikido_freq_wk3'],
    'bpaq_box':	['bpaq_box_freq_wk',	'bpaq_box_freq_wk2',	'bpaq_box_freq_wk3'],
    'bpaq_hapk':	['bpaq_hapk_freq_wk',	'bpaq_hapk_freq_wk2',	'bpaq_hapk_freq_wk3'],
    'bpaq_judo':	['bpaq_judo_freq_wk',	'bpaq_judo_freq_wk2',	'bpaq_judo_freq_wk3'],
    'bpaq_karate':	['bpaq_karate_freq_wk',	'bpaq_karate_freq_wk2',	'bpaq_karate_freq_wk3'],
    'bpaq_kick':	['bpaq_kick_freq_wk',	'bpaq_kick_freq_wk2',	'bpaq_kick_freq_wk3'],
    'bpaq_kungfu':	['bpaq_kungfu_freq_wk',	'bpaq_kungfu_freq_wk2',	'bpaq_kungfu_freq_wk3'],
    'bpaq_taekwondo':	['bpaq_taekwondo_freq_wk',	'bpaq_taekwondo_freq_wk2',	'bpaq_taekwondo_freq_wk3'],
    'bpaq_taichi':	['bpaq_taichi_freq_wk',	'bpaq_taichi_freq_wk2',	'bpaq_taichi_freq_wk3'],
    'bpaq_wrest':	['bpaq_wrest_freq_wk',	'bpaq_wrest_freq_wk2',	'bpaq_wrest_freq_wk3'],
    'bpaq_occ_light':	['bpaq_occ_light_freq_wk',	'bpaq_occ_light_freq_wk2',	'bpaq_occ_light_freq_wk3'],
    'bpaq_occ_heavy':	['bpaq_occ_heavy_freq_wk',	'bpaq_occ_heavy_freq_wk2',	'bpaq_occ_heavy_freq_wk3'],
    'bpaq_bad':	['bpaq_bad_freq_wk',	'bpaq_bad_freq_wk2',	'bpaq_bad_freq_wk3'],
    'bpaq_ping':	['bpaq_ping_freq_wk',	'bpaq_ping_freq_wk2',	'bpaq_ping_freq_wk3'],
    'bpaq_rac_ball':	['bpaq_rac_ball_freq_wk',	'bpaq_rac_ball_freq_wk2',	'bpaq_rac_ball_freq_wk3'],
    'bpaq_squash':	['bpaq_squash_freq_wk',	'bpaq_squash_freq_wk2',	'bpaq_squash_freq_wk3'],
    'bpaq_tennis':	['bpaq_tennis_freq_wk',	'bpaq_tennis_freq_wk2',	'bpaq_tennis_freq_wk3'],
    'bpaq_horse':	['bpaq_horse_freq_wk',	'bpaq_horse_freq_wk2',	'bpaq_horse_freq_wk3'],
    'bpaq_motor':	['bpaq_motor_freq_wk',	'bpaq_motor_freq_wk2',	'bpaq_motor_freq_wk3'],
    'bpaq_beach_spr':	['bpaq_beach_spr_freq_wk',	'bpaq_beach_spr_freq_wk2',	'bpaq_beach_spr_freq_wk3'],
    'bpaq_cross_count':	['bpaq_cross_count_freq_wk',	'bpaq_cross_count_freq_wk2',	'bpaq_cross_count_freq_wk3'],
    'bpaq_marat':	['bpaq_marat_freq_wk',	'bpaq_marat_freq_wk2',	'bpaq_marat_freq_wk3'],
    'bpaq_mid_dist':	['bpaq_mid_dist_freq_wk',	'bpaq_mid_dist_freq_wk2',	'bpaq_mid_dist_freq_wk3'],
    'bpaq_jog':	['bpaq_jog_freq_wk',	'bpaq_jog_freq_wk2',	'bpaq_jog_freq_wk3'],
    'bpaq_sprint':	['bpaq_sprint_freq_wk',	'bpaq_sprint_freq_wk2',	'bpaq_sprint_freq_wk3'],
    'bpaq_hock':	['bpaq_hock_freq_wk',	'bpaq_hock_freq_wk2',	'bpaq_hock_freq_wk3'],
    'bpaq_ice_skate':	['bpaq_ice_skate_freq_wk',	'bpaq_ice_skate_freq_wk2',	'bpaq_ice_skate_freq_wk3'],
    'bpaq_fig_skate':	['bpaq_fig_skate_freq_wk',	'bpaq_fig_skate_freq_wk2',	'bpaq_fig_skate_freq_wk3'],
    'bpaq_roll_blade':	['bpaq_roll_blade_freq_wk',	'bpaq_roll_blade_freq_wk2',	'bpaq_roll_blade_freq_wk3'],
    'bpaq_roll_derby':	['bpaq_roll_derby_freq_wk',	'bpaq_roll_derby_freq_wk2',	'bpaq_roll_derby_freq_wk3'],
    'bpaq_roll_skate':	['bpaq_roll_skate_freq_wk',	'bpaq_roll_skate_freq_wk2',	'bpaq_roll_skate_freq_wk3'],
    'bpaq_scoot':	['bpaq_scoot_freq_wk',	'bpaq_scoot_freq_wk2',	'bpaq_scoot_freq_wk3'],
    'bpaq_skateboard':	['bpaq_skateboard_freq_wk',	'bpaq_skateboard_freq_wk2',	'bpaq_skateboard_freq_wk3'],
    'bpaq_cross_ski':	['bpaq_cross_ski_freq_wk',	'bpaq_cross_ski_freq_wk2',	'bpaq_cross_ski_freq_wk3'],
    'bpaq_snowshoe':	['bpaq_snowshoe_freq_wk',	'bpaq_snowshoe_freq_wk2',	'bpaq_snowshoe_freq_wk3'],
    'bpaq_ski':	['bpaq_ski_freq_wk',	'bpaq_ski_freq_wk2',	'bpaq_ski_freq_wk3'],
    'bpaq_sled':	['bpaq_sled_freq_wk',	'bpaq_sled_freq_wk2',	'bpaq_sled_freq_wk3'],
    'bpaq_snowboard':	['bpaq_snowboard_freq_wk',	'bpaq_snowboard_freq_wk2',	'bpaq_snowboard_freq_wk3'],
    'bpaq_kite_surf':	['bpaq_kite_surf_freq_wk',	'bpaq_kite_surf_freq_wk2',	'bpaq_kite_surf_freq_wk3'],
    'bpaq_surf':	['bpaq_surf_freq_wk',	'bpaq_surf_freq_wk2',	'bpaq_surf_freq_wk3'],
    'bpaq_surf_comp':	['bpaq_surf_comp_freq_wk',	'bpaq_surf_comp_freq_wk2',	'bpaq_surf_comp_freq_wk3'],
    'bpaq_windsurf':	['bpaq_windsurf_freq_wk',	'bpaq_windsurf_freq_wk2',	'bpaq_windsurf_freq_wk3'],
    'bpaq_dive':	['bpaq_dive_freq_wk',	'bpaq_dive_freq_wk2',	'bpaq_dive_freq_wk3'],
    'bpaq_swim_rec':	['bpaq_swim_rec_freq_wk',	'bpaq_swim_rec_freq_wk2',	'bpaq_swim_rec_freq_wk3'],
    'bpaq_swim_sprint':	['bpaq_swim_sprint_freq_wk',	'bpaq_swim_sprint_freq_wk2',	'bpaq_swim_sprint_freq_wk3'],
    'bpaq_swim_lap':	['bpaq_swim_lap_freq_wk',	'bpaq_swim_lap_freq_wk2',	'bpaq_swim_lap_freq_wk3'],
    'bpaq_scuba':	['bpaq_scuba_freq_wk',	'bpaq_scuba_freq_wk2',	'bpaq_scuba_freq_wk3'],
    'bpaq_snorkel':	['bpaq_snorkel_freq_wk',	'bpaq_snorkel_freq_wk2',	'bpaq_snorkel_freq_wk3'],
    'bpaq_syn_swim':	['bpaq_syn_swim_freq_wk',	'bpaq_syn_swim_freq_wk2',	'bpaq_syn_swim_freq_wk3'],
    'bpaq_water_aerob':	['bpaq_water_aerob_freq_wk',	'bpaq_water_aerob_freq_wk2',	'bpaq_water_aerob_freq_wk3'],
    'bpaq_water_polo':	['bpaq_water_polo_freq_wk',	'bpaq_water_polo_freq_wk2',	'bpaq_water_polo_freq_wk3'],
    'bpaq_bball':	['bpaq_bball_freq_wk',	'bpaq_bball_freq_wk2',	'bpaq_bball_freq_wk3'],
    'bpaq_beachvol':	['bpaq_beachvol_freq_w',	'bpaq_beachvol_freq_wk2',	'bpaq_beachvol_freq_wk3'],
    'bpaq_handball':	['bpaq_handball_freq_wk',	'bpaq_handball_freq_wk2',	'bpaq_handball_freq_wk3'],
    'bpaq_netball':	['bpaq_netball_freq_wk',	'bpaq_netball_freq_wk2',	'bpaq_netball_freq_wk3'],
    'bpaq_ult_fris':	['bpaq_ult_fris_freq_wk',	'bpaq_ult_fris_freq_wk2',	'bpaq_ult_fris_freq_wk3'],
    'bpaq_volley':	['bpaq_volley_freq_wk',	'bpaq_volley_freq_wk2',	'bpaq_volley_freq_wk3'],
    'bpaq_tri_rec':	['bpaq_tri_rec_freq_wk',	'bpaq_tri_rec_freq_wk2',	'bpaq_tri_rec_freq_wk3'],
    'bpaq_tri_comp':	['bpaq_tri_comp_freq_wk',	'bpaq_tri_comp_freq_wk2',	'bpaq_tri_comp_freq_wk3'],
    'bpaq_hike':	['bpaq_hike_freq_wk',	'bpaq_hike_freq_wk2',	'bpaq_hike_freq_wk3'],
    'bpaq_walk':	['bpaq_walk_freq_wk',	'bpaq_walk_freq_wk2',	'bpaq_walk_freq_wk3'],
    'bpaq_mount':	['bpaq_mount_freq_wk',	'bpaq_mount_freq_wk2',	'bpaq_mount_freq_wk3'],
    'bpaq_pow_walk':	['bpaq_pow_walk_freq_wk',	'bpaq_race_walk_freq_wk2',	'bpaq_race_walk_freq_wk3'],
    'bpaq_race_walk':	['bpaq_race_walk_freq_wk',	'bpaq_pow_walk_freq_wk2',	'bpaq_pow_walk_freq_wk3'],
    'bpaq_stair_cl':	['bpaq_stair_cl_freq_wk',	'bpaq_stair_cl_freq_wk2',	'bpaq_stair_cl_freq_wk3'],
    'bpaq_body_board':	['bpaq_body_board_freq_wk',	'bpaq_body_board_freq_wk2',	'bpaq_body_board_freq_wk3'],
    'bpaq_canoe':	['bpaq_canoe_freq_wk',	'bpaq_canoe_freq_wk2',	'bpaq_canoe_freq_wk3'],
    'bpaq_dragon':	['bpaq_dragon_freq_wk',	'bpaq_dragon_freq_wk2',	'bpaq_dragon_freq_wk3'],
    'bpaq_kayak':	['bpaq_kayak_freq_wk',	'bpaq_kayak_freq_wk2',	'bpaq_kayak_freq_wk3'],
    'bpaq_kite_surf1':	['bpaq_kite_surf1_freq_wk',	'bpaq_kite_surf1_freq_wk2',	'bpaq_kite_surf1_freq_wk3'],
    'bpaq_paddle':	['bpaq_paddle_freq_wk',	'bpaq_paddle_freq_wk2',	'bpaq_paddle_freq_wk3'],
    'bpaq_row':	['bpaq_row_freq_wk',	'bpaq_row_freq_wk2',	'bpaq_row_freq_wk3'],
    'bpaq_sail':	['bpaq_sail_freq_wk',	'bpaq_sail_freq_wk2',	'bpaq_sail_freq_wk3'],
    'bpaq_skull':	['bpaq_skull_freq_wk',	'bpaq_skull_freq_wk2',	'bpaq_skull_freq_wk3'],
    'bpaq_surf1':	['bpaq_surf1_freq_wk',	'bpaq_surf1_freq_wk2',	'bpaq_surf1_freq_wk3'],
    'bpaq_surf_comp1':	['bpaq_surf_comp1_freq_wk',	'bpaq_surf_comp1_freq_wk2',	'bpaq_surf_comp1_freq_wk3'],
    'bpaq_wake':	['bpaq_wake_freq_wk',	'bpaq_wake_freq_wk2',	'bpaq_wake_freq_wk3'],
    'bpaq_water_ski':	['bpaq_water_ski_freq_wk',	'bpaq_water_ski_freq_wk2',	'bpaq_water_ski_freq_wk3'],
    'bpaq_windsurf1':	['bpaq_windsurf1_freq_wk',	'bpaq_windsurf1_freq_wk2',	'bpaq_windsurf1_freq_wk3'],
    'bpaq_low_imp':	['bpaq_low_imp_freq_wk',	'bpaq_low_imp_freq_wk2',	'bpaq_low_imp_freq_wk3'],
    'bpaq_mod_imp':	['bpaq_mod_imp_freq_wk',	'bpaq_mod_imp_freq_wk2',	'bpaq_mod_imp_freq_wk3'],
    'bpaq_high_imp':	['bpaq_high_imp_freq_wk',	'bpaq_high_imp_freq_wk2',	'bpaq_high_imp_freq_wk3']
  }
  return myDict
  
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
    if not (isinstance(freq_wk,float) or isinstance(freq_wk,int)):
        print('WARNING: Variable freq_wk is neither float nor int.')
        print('         Variable freq_wk = ',freq_wk)
        print('         Setting freq_wk to 0')
        freq_wk = 0

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

def individual_profile_to_dataframe(profile):
    
    d = {
      'record_id': ['tmp'],'age_enroll': [''],'redcap_event_name': [''],'redcap_survey_identifier': [''],'bonespecific_physical_activity_questionnaire_bpaq_timestamp': [''],'bpaq_grp_ath': [''],'bpaq_grp_ball': [''],'bpaq_grp_bowl': [''],'bpaq_grp_climb': [''],'bpaq_grp_cycle': [''],'bpaq_grp_dance': [''],'bpaq_grp_football': [''],'bpaq_grp_gymnastics': [''],'bpaq_grp_gym': [''],'bpaq_grp_house': [''],'bpaq_grp_jump': [''],'bpaq_grp_lifting': [''],'bpaq_grp_ma': [''],'bpaq_grp_occ_act': [''],'bpaq_grp_rac_sport': [''],'bpaq_grp_riding': [''],'bpaq_grp_run': [''],'bpaq_grp_skate': [''],'bpaq_grp_snow': [''],'bpaq_grp_surf': [''],'bpaq_grp_swim': [''],'bpaq_grp_throw': [''],'bpaq_grp_tri': [''],'bpaq_grp_walk': [''],'bpaq_grp_water_sport': [''],'bpaq_grp_other': [''],'bpaq_ath_jump': [''],'bpaq_ath_mid': [''],'bpaq_ath_throw': [''],'bpaq_ath_hurd': [''],'bpaq_ath_junior': [''],'bpaq_jump_freq_wk': [''],'bpaq_mid_freq_wk': [''],'bpaq_throw_freq_wk': [''],'bpaq_hurd_freq_wk': [''],'bpaq_junior_freq_wk': [''],'bpaq_ball_baseball': [''],'bpaq_ball_cric': [''],'bpaq_ball_f_hoc': [''],'bpaq_ball_golf_walk': [''],'bpaq_ball_golf_car': [''],'bpaq_ball_ice_hoc': [''],'bpaq_ball_lacr': [''],'bpaq_ball_soft': [''],'bpaq_ball_tball': [''],'bpaq_baseball_freq_wk': [''],'bpaq_cric_freq_wk': [''],'bpaq_f_hoc_freq_wk': [''],'bpaq_golf_walk_freq_wk': [''],'bpaq_golf_car_freq_wk': [''],'bpaq_ice_hoc_freq_wk': [''],'bpaq_lacr_freq_wk': [''],'bpaq_soft_freq_wk': [''],'bpaq_tball_freq_wk': [''],'bpaq_lawn_bowl': [''],'bpaq_10pin': [''],'bpaq_lawn_bowl_freq_wk': [''],'bpaq_10pin_freq_wk': [''],'bpaq_rock': [''],'bpaq_gym_climb': [''],'bpaq_boulder': [''],'bpaq_rock_freq_wk': [''],'bpaq_gym_climb_freq_wk': [''],'bpaq_boulder_freq_wk': [''],'bpaq_cycle_rec': [''],'bpaq_cycle_sprint': [''],'bpaq_cycle_end': [''],'bpaq_cycle_rec_freq_wk': [''],'bpaq_cycle_sprint_freq_wk': [''],'bpaq_cycle_end_freq_wk': [''],'bpaq_ballet': [''],'bpaq_ballroom': [''],'bpaq_cheer': [''],'bpaq_cont': [''],'bpaq_high': [''],'bpaq_hiphop': [''],'bpaq_jazz': [''],'bpaq_line': [''],'bpaq_tap': [''],'bpaq_ballet_freq_wk': [''],'bpaq_ballroom_freq_wk': [''],'bpaq_cheer_freq_wk': [''],'bpaq_cont_freq_wk': [''],'bpaq_high_freq_wk': [''],'bpaq_hiphop_freq_wk': [''],'bpaq_jazz_freq_wk': [''],'bpaq_line_freq_wk': [''],'bpaq_tap_freq_wk': [''],'bpaq_au_foot': [''],'bpaq_flag_foot': [''],'bpaq_oz_tag': [''],'bpaq_rugby': [''],'bpaq_rugby_un': [''],'bpaq_soccer': [''],'bpaq_foot': [''],'bpaq_au_foot_freq_wk': [''],'bpaq_flag_foot_freq_wk': [''],'bpaq_oz_tag_freq_wk': [''],'bpaq_rugby_freq_wk': [''],'bpaq_rugby_un_freq_wk': [''],'bpaq_soccer_freq_wk': [''],'bpaq_foot_freq_wk': [''],'bpaq_acro': [''],'bpaq_art': [''],'bpaq_dev': [''],'bpaq_rhyt': [''],'bpaq_tramp': [''],'bpaq_acro_freq_wk': [''],'bpaq_art_freq_wk': [''],'bpaq_dev_freq_wk': [''],'bpaq_rhyt_freq_wk': [''],'bpaq_tramp_freq_wk': [''],'bpaq_aero_high': [''],'bpaq_aero_low': [''],'bpaq_boot': [''],'bpaq_cross': [''],'bpaq_elip': [''],'bpaq_high_train': [''],'bpaq_pilates': [''],'bpaq_res_upp_low': [''],'bpaq_res_upp': [''],'bpaq_res_low': [''],'bpaq_res_light': [''],'bpaq_res_body': [''],'bpaq_skip': [''],'bpaq_spin': [''],'bpaq_stair': [''],'bpaq_tread_run': [''],'bpaq_tread_walk': [''],'bpaq_yoga': [''],'bpaq_zumba': [''],'bpaq_aero_high_freq_wk': [''],'bpaq_aero_low_freq_wk': [''],'bpaq_boot_freq_wk': [''],'bpaq_cross_freq_wk': [''],'bpaq_elip_freq_wk': [''],'bpaq_high_train_freq_wk': [''],'bpaq_pilates_freq_wk': [''],'bpaq_res_upp_low_freq_wk': [''],'bpaq_res_upp_freq_wk': [''],'bpaq_res_low_freq_wk': [''],'bpaq_res_light_freq_wk': [''],'bpaq_res_body_freq_wk': [''],'bpaq_skip_freq_wk': [''],'bpaq_spin_freq_wk': [''],'bpaq_stair_freq_wk': [''],'bpaq_tread_run_freq_wk': [''],'bpaq_tread_walk_freq_wk': [''],'bpaq_yoga_freq_wk': [''],'bpaq_zumba_freq_wk': [''],'bpaq_house': [''],'bpaq_gard': [''],'bpaq_house_freq_wk': [''],'bpaq_gard_freq_wk': [''],'bpaq_jumprope': [''],'bpaq_plyo': [''],'bpaq_jumprope_freq_wk': [''],'bpaq_plyo_freq_wk': [''],'bpaq_power_lift': [''],'bpaq_res_heavy': [''],'bpaq_res_light1': [''],'bpaq_body_wt': [''],'bpaq_power_lift_freq_wk': [''],'bpaq_res_heavy_freq_wk': [''],'bpaq_res_light1_freq_wk': [''],'bpaq_body_wt_freq_wk': [''],'bpaq_aikido': [''],'bpaq_box': [''],'bpaq_hapk': [''],'bpaq_judo': [''],'bpaq_karate': [''],'bpaq_kick': [''],'bpaq_kungfu': [''],'bpaq_taekwondo': [''],'bpaq_taichi': [''],'bpaq_wrest': [''],'bpaq_aikido_freq_wk': [''],'bpaq_box_freq_wk': [''],'bpaq_hapk_freq_wk': [''],'bpaq_judo_freq_wk': [''],'bpaq_karate_freq_wk': [''],'bpaq_kick_freq_wk': [''],'bpaq_kungfu_freq_wk': [''],'bpaq_taekwondo_freq_wk': [''],'bpaq_taichi_freq_wk': [''],'bpaq_wrest_freq_wk': [''],'bpaq_occ_light': [''],'bpaq_occ_heavy': [''],'bpaq_occ_light_freq_wk': [''],'bpaq_occ_heavy_freq_wk': [''],'bpaq_bad': [''],'bpaq_ping': [''],'bpaq_rac_ball': [''],'bpaq_squash': [''],'bpaq_tennis': [''],'bpaq_bad_freq_wk': [''],'bpaq_ping_freq_wk': [''],'bpaq_rac_ball_freq_wk': [''],'bpaq_squash_freq_wk': [''],'bpaq_tennis_freq_wk': [''],'bpaq_horse': [''],'bpaq_motor': [''],'bpaq_horse_freq_wk': [''],'bpaq_motor_freq_wk': [''],'bpaq_beach_spr': [''],'bpaq_cross_count': [''],'bpaq_marat': [''],'bpaq_mid_dist': [''],'bpaq_jog': [''],'bpaq_sprint': [''],'bpaq_beach_spr_freq_wk': [''],'bpaq_cross_count_freq_wk': [''],'bpaq_marat_freq_wk': [''],'bpaq_mid_dist_freq_wk': [''],'bpaq_jog_freq_wk': [''],'bpaq_sprint_freq_wk': [''],'bpaq_hock': [''],'bpaq_ice_skate': [''],'bpaq_fig_skate': [''],'bpaq_roll_blade': [''],'bpaq_roll_derby': [''],'bpaq_roll_skate': [''],'bpaq_scoot': [''],'bpaq_skateboard': [''],'bpaq_hock_freq_wk': [''],'bpaq_ice_skate_freq_wk': [''],'bpaq_fig_skate_freq_wk': [''],'bpaq_roll_blade_freq_wk': [''],'bpaq_roll_derby_freq_wk': [''],'bpaq_roll_skate_freq_wk': [''],'bpaq_scoot_freq_wk': [''],'bpaq_skateboard_freq_wk': [''],'bpaq_cross_ski': [''],'bpaq_snowshoe': [''],'bpaq_ski': [''],'bpaq_sled': [''],'bpaq_snowboard': [''],'bpaq_cross_ski_freq_wk': [''],'bpaq_snowshoe_freq_wk': [''],'bpaq_ski_freq_wk': [''],'bpaq_sled_freq_wk': [''],'bpaq_snowboard_freq_wk': [''],'bpaq_kite_surf': [''],'bpaq_surf': [''],'bpaq_surf_comp': [''],'bpaq_windsurf': [''],'bpaq_kite_surf_freq_wk': [''],'bpaq_surf_freq_wk': [''],'bpaq_surf_comp_freq_wk': [''],'bpaq_windsurf_freq_wk': [''],'bpaq_dive': [''],'bpaq_swim_rec': [''],'bpaq_swim_sprint': [''],'bpaq_swim_lap': [''],'bpaq_scuba': [''],'bpaq_snorkel': [''],'bpaq_syn_swim': [''],'bpaq_water_aerob': [''],'bpaq_water_polo': [''],'bpaq_dive_freq_wk': [''],'bpaq_swim_rec_freq_wk': [''],'bpaq_swim_sprint_freq_wk': [''],'bpaq_swim_lap_freq_wk': [''],'bpaq_scuba_freq_wk': [''],'bpaq_snorkel_freq_wk': [''],'bpaq_syn_swim_freq_wk': [''],'bpaq_water_aerob_freq_wk': [''],'bpaq_water_polo_freq_wk': [''],'bpaq_bball': [''],'bpaq_beachvol': [''],'bpaq_handball': [''],'bpaq_netball': [''],'bpaq_ult_fris': [''],'bpaq_volley': [''],'bpaq_bball_freq_wk': [''],'bpaq_beachvol_freq_w': [''],'bpaq_handball_freq_wk': [''],'bpaq_netball_freq_wk': [''],'bpaq_ult_fris_freq_wk': [''],'bpaq_volley_freq_wk': [''],'bpaq_tri_rec': [''],'bpaq_tri_comp': [''],'bpaq_tri_rec_freq_wk': [''],'bpaq_tri_comp_freq_wk': [''],'bpaq_hike': [''],'bpaq_walk': [''],'bpaq_mount': [''],'bpaq_pow_walk': [''],'bpaq_race_walk': [''],'bpaq_stair_cl': [''],'bpaq_hike_freq_wk': [''],'bpaq_walk_freq_wk': [''],'bpaq_mount_freq_wk': [''],'bpaq_pow_walk_freq_wk': [''],'bpaq_race_walk_freq_wk': [''],'bpaq_stair_cl_freq_wk': [''],'bpaq_body_board': [''],'bpaq_canoe': [''],'bpaq_dragon': [''],'bpaq_kayak': [''],'bpaq_kite_surf1': [''],'bpaq_paddle': [''],'bpaq_row': [''],'bpaq_sail': [''],'bpaq_skull': [''],'bpaq_surf1': [''],'bpaq_surf_comp1': [''],'bpaq_wake': [''],'bpaq_water_ski': [''],'bpaq_windsurf1': [''],'bpaq_body_board_freq_wk': [''],'bpaq_canoe_freq_wk': [''],'bpaq_dragon_freq_wk': [''],'bpaq_kayak_freq_wk': [''],'bpaq_kite_surf1_freq_wk': [''],'bpaq_paddle_freq_wk': [''],'bpaq_row_freq_wk': [''],'bpaq_sail_freq_wk': [''],'bpaq_skull_freq_wk': [''],'bpaq_surf1_freq_wk': [''],'bpaq_surf_comp1_freq_wk': [''],'bpaq_wake_freq_wk': [''],'bpaq_water_ski_freq_wk': [''],'bpaq_windsurf1_freq_wk': [''],'bpaq_low_imp': [''],'bpaq_mod_imp': [''],'bpaq_high_imp': [''],'bpaq_low_imp_freq_wk': [''],'bpaq_mod_imp_freq_wk': [''],'bpaq_high_imp_freq_wk': [''],'bpaq_grp_ath2': [''],'bpaq_grp_ball2': [''],'bpaq_grp_bowl2': [''],'bpaq_grp_climb2': [''],'bpaq_grp_cycle2': [''],'bpaq_grp_dance2': [''],'bpaq_grp_football2': [''],'bpaq_grp_gymnastics2': [''],'bpaq_grp_gym2': [''],'bpaq_grp_house2': [''],'bpaq_grp_jump2': [''],'bpaq_grp_lifting2': [''],'bpaq_grp_ma2': [''],'bpaq_grp_occ_act2': [''],'bpaq_grp_rac_sport2': [''],'bpaq_grp_riding2': [''],'bpaq_grp_run2': [''],'bpaq_grp_skate2': [''],'bpaq_grp_snow2': [''],'bpaq_grp_surf2': [''],'bpaq_grp_swim2': [''],'bpaq_grp_throw2': [''],'bpaq_grp_tri2': [''],'bpaq_grp_walk2': [''],'bpaq_grp_water_sport2': [''],'bpaq_grp_other2': [''],'bpaq_ath_jump2': [''],'bpaq_ath_mid2': [''],'bpaq_ath_throw2': [''],'bpaq_ath_hurd2': [''],'bpaq_ath_junior2': [''],'bpaq_jump_freq_wk2': [''],'bpaq_mid_freq_wk2': [''],'bpaq_throw_freq_wk2': [''],'bpaq_hurd_freq_wk2': [''],'bpaq_junior_freq_wk2': [''],'bpaq_ball_baseball2': [''],'bpaq_ball_cric2': [''],'bpaq_ball_f_hoc2': [''],'bpaq_ball_golf_walk2': [''],'bpaq_ball_golf_car2': [''],'bpaq_ball_ice_hoc2': [''],'bpaq_ball_lacr2': [''],'bpaq_ball_soft2': [''],'bpaq_ball_tball2': [''],'bpaq_baseball_freq_wk2': [''],'bpaq_cric_freq_wk2': [''],'bpaq_f_hoc_freq_wk2': [''],'bpaq_golf_walk_freq_wk2': [''],'bpaq_golf_car_freq_wk2': [''],'bpaq_ice_hoc_freq_wk2': [''],'bpaq_lacr_freq_wk2': [''],'bpaq_soft_freq_wk2': [''],'bpaq_tball_freq_wk2': [''],'bpaq_lawn_bowl2': [''],'bpaq_10pin2': [''],'bpaq_lawn_bowl_freq_wk2': [''],'bpaq_10pin_freq_wk2': [''],'bpaq_rock2': [''],'bpaq_gym_climb2': [''],'bpaq_boulder2': [''],'bpaq_rock_freq_wk2': [''],'bpaq_gym_climb_freq_wk2': [''],'bpaq_boulder_freq_wk2': [''],'bpaq_cycle_rec2': [''],'bpaq_cycle_sprint2': [''],'bpaq_cycle_end2': [''],'bpaq_cycle_rec_freq_wk2': [''],'bpaq_cycle_sprint_freq_wk2': [''],'bpaq_cycle_end_freq_wk2': [''],'bpaq_ballet2': [''],'bpaq_ballroom2': [''],'bpaq_cheer2': [''],'bpaq_cont2': [''],'bpaq_high2': [''],'bpaq_hiphop2': [''],'bpaq_jazz2': [''],'bpaq_line2': [''],'bpaq_tap2': [''],'bpaq_ballet_freq_wk2': [''],'bpaq_ballroom_freq_wk2': [''],'bpaq_cheer_freq_wk2': [''],'bpaq_cont_freq_wk2': [''],'bpaq_high_freq_wk2': [''],'bpaq_hiphop_freq_wk2': [''],'bpaq_jazz_freq_wk2': [''],'bpaq_line_freq_wk2': [''],'bpaq_tap_freq_wk2': [''],'bpaq_au_foot2': [''],'bpaq_flag_foot2': [''],'bpaq_oz_tag2': [''],'bpaq_rugby2': [''],'bpaq_rugby_un2': [''],'bpaq_soccer2': [''],'bpaq_foot2': [''],'bpaq_au_foot_freq_wk2': [''],'bpaq_flag_foot_freq_wk2': [''],'bpaq_oz_tag_freq_wk2': [''],'bpaq_rugby_freq_wk2': [''],'bpaq_rugby_un_freq_wk2': [''],'bpaq_soccer_freq_wk2': [''],'bpaq_foot_freq_wk2': [''],'bpaq_acro2': [''],'bpaq_art2': [''],'bpaq_dev2': [''],'bpaq_rhyt2': [''],'bpaq_tramp2': [''],'bpaq_acro_freq_wk2': [''],'bpaq_art_freq_wk2': [''],'bpaq_dev_freq_wk2': [''],'bpaq_rhyt_freq_wk2': [''],'bpaq_tramp_freq_wk2': [''],'bpaq_aero_high2': [''],'bpaq_aero_low2': [''],'bpaq_boot2': [''],'bpaq_cross2': [''],'bpaq_elip2': [''],'bpaq_high_train2': [''],'bpaq_pilates2': [''],'bpaq_res_upp_low2': [''],'bpaq_res_upp2': [''],'bpaq_res_low2': [''],'bpaq_res_light2': [''],'bpaq_res_body2': [''],'bpaq_skip2': [''],'bpaq_spin2': [''],'bpaq_stair2': [''],'bpaq_tread_run2': [''],'bpaq_tread_walk2': [''],'bpaq_yoga2': [''],'bpaq_zumba2': [''],'bpaq_aero_high_freq_wk2': [''],'bpaq_aero_low_freq_wk2': [''],'bpaq_boot_freq_wk2': [''],'bpaq_cross_freq_wk2': [''],'bpaq_elip_freq_wk2': [''],'bpaq_high_train_freq_wk2': [''],'bpaq_pilates_freq_wk2': [''],'bpaq_res_upp_low_freq_wk2': [''],'bpaq_res_upp_freq_wk2': [''],'bpaq_res_low_freq_wk2': [''],'bpaq_res_light_freq_wk2': [''],'bpaq_res_body_freq_wk2': [''],'bpaq_skip_freq_wk2': [''],'bpaq_spin_freq_wk2': [''],'bpaq_stair_freq_wk2': [''],'bpaq_tread_run_freq_wk2': [''],'bpaq_tread_walk_freq_wk2': [''],'bpaq_yoga_freq_wk2': [''],'bpaq_zumba_freq_wk2': [''],'bpaq_house2': [''],'bpaq_gard2': [''],'bpaq_house_freq_wk2': [''],'bpaq_gard_freq_wk2': [''],'bpaq_jumprope2': [''],'bpaq_plyo2': [''],'bpaq_jumprope_freq_wk2': [''],'bpaq_plyo_freq_wk2': [''],'bpaq_power_lift2': [''],'bpaq_res_heavy2': [''],'bpaq_res_light1_2': [''],'bpaq_body_wt2': [''],'bpaq_power_lift_freq_wk2': [''],'bpaq_res_heavy_freq_wk2': [''],'bpaq_res_light1_freq_wk2': [''],'bpaq_body_wt_freq_wk2': [''],'bpaq_aikido2': [''],'bpaq_box2': [''],'bpaq_hapk2': [''],'bpaq_judo2': [''],'bpaq_karate2': [''],'bpaq_kick2': [''],'bpaq_kungfu2': [''],'bpaq_taekwondo2': [''],'bpaq_taichi2': [''],'bpaq_wrest2': [''],'bpaq_aikido_freq_wk2': [''],'bpaq_box_freq_wk2': [''],'bpaq_hapk_freq_wk2': [''],'bpaq_judo_freq_wk2': [''],'bpaq_karate_freq_wk2': [''],'bpaq_kick_freq_wk2': [''],'bpaq_kungfu_freq_wk2': [''],'bpaq_taekwondo_freq_wk2': [''],'bpaq_taichi_freq_wk2': [''],'bpaq_wrest_freq_wk2': [''],'bpaq_occ_light2': [''],'bpaq_occ_heavy2': [''],'bpaq_occ_light_freq_wk2': [''],'bpaq_occ_heavy_freq_wk2': [''],'bpaq_bad2': [''],'bpaq_ping2': [''],'bpaq_rac_ball2': [''],'bpaq_squash2': [''],'bpaq_tennis2': [''],'bpaq_bad_freq_wk2': [''],'bpaq_ping_freq_wk2': [''],'bpaq_rac_ball_freq_wk2': [''],'bpaq_squash_freq_wk2': [''],'bpaq_tennis_freq_wk2': [''],'bpaq_horse2': [''],'bpaq_motor2': [''],'bpaq_horse_freq_wk2': [''],'bpaq_motor_freq_wk2': [''],'bpaq_beach_spr2': [''],'bpaq_cross_count2': [''],'bpaq_marat2': [''],'bpaq_mid_dist2': [''],'bpaq_jog2': [''],'bpaq_sprint2': [''],'bpaq_beach_spr_freq_wk2': [''],'bpaq_cross_count_freq_wk2': [''],'bpaq_marat_freq_wk2': [''],'bpaq_mid_dist_freq_wk2': [''],'bpaq_jog_freq_wk2': [''],'bpaq_sprint_freq_wk2': [''],'bpaq_hock2': [''],'bpaq_ice_skate2': [''],'bpaq_fig_skate2': [''],'bpaq_roll_blade2': [''],'bpaq_roll_derby2': [''],'bpaq_roll_skate2': [''],'bpaq_scoot2': [''],'bpaq_skateboard2': [''],'bpaq_hock_freq_wk2': [''],'bpaq_ice_skate_freq_wk2': [''],'bpaq_fig_skate_freq_wk2': [''],'bpaq_roll_blade_freq_wk2': [''],'bpaq_roll_derby_freq_wk2': [''],'bpaq_roll_skate_freq_wk2': [''],'bpaq_scoot_freq_wk2': [''],'bpaq_skateboard_freq_wk2': [''],'bpaq_cross_ski2': [''],'bpaq_snowshoe2': [''],'bpaq_ski2': [''],'bpaq_sled2': [''],'bpaq_snowboard2': [''],'bpaq_cross_ski_freq_wk2': [''],'bpaq_snowshoe_freq_wk2': [''],'bpaq_ski_freq_wk2': [''],'bpaq_sled_freq_wk2': [''],'bpaq_snowboard_freq_wk2': [''],'bpaq_kite_surf2': [''],'bpaq_surf2': [''],'bpaq_surf_comp2': [''],'bpaq_windsurf2': [''],'bpaq_kite_surf_freq_wk2': [''],'bpaq_surf_freq_wk2': [''],'bpaq_surf_comp_freq_wk2': [''],'bpaq_windsurf_freq_wk2': [''],'bpaq_dive2': [''],'bpaq_swim_rec2': [''],'bpaq_swim_sprint2': [''],'bpaq_swim_lap2': [''],'bpaq_scuba2': [''],'bpaq_snorkel2': [''],'bpaq_syn_swim2': [''],'bpaq_water_aerob2': [''],'bpaq_water_polo2': [''],'bpaq_dive_freq_wk2': [''],'bpaq_swim_rec_freq_wk2': [''],'bpaq_swim_sprint_freq_wk2': [''],'bpaq_swim_lap_freq_wk2': [''],'bpaq_scuba_freq_wk2': [''],'bpaq_snorkel_freq_wk2': [''],'bpaq_syn_swim_freq_wk2': [''],'bpaq_water_aerob_freq_wk2': [''],'bpaq_water_polo_freq_wk2': [''],'bpaq_bball2': [''],'bpaq_beachvol2': [''],'bpaq_handball2': [''],'bpaq_netball2': [''],'bpaq_ult_fris2': [''],'bpaq_volley2': [''],'bpaq_bball_freq_wk2': [''],'bpaq_beachvol_freq_wk2': [''],'bpaq_handball_freq_wk2': [''],'bpaq_netball_freq_wk2': [''],'bpaq_ult_fris_freq_wk2': [''],'bpaq_volley_freq_wk2': [''],'bpaq_tri_rec2': [''],'bpaq_tri_comp2': [''],'bpaq_tri_rec_freq_wk2': [''],'bpaq_tri_comp_freq_wk2': [''],'bpaq_hike2': [''],'bpaq_walk2': [''],'bpaq_mount2': [''],'bpaq_pow_walk2': [''],'bpaq_race_walk2': [''],'bpaq_stair_cl2': [''],'bpaq_hike_freq_wk2': [''],'bpaq_walk_freq_wk2': [''],'bpaq_mount_freq_wk2': [''],'bpaq_race_walk_freq_wk2': [''],'bpaq_pow_walk_freq_wk2': [''],'bpaq_stair_cl_freq_wk2': [''],'bpaq_body_board2': [''],'bpaq_canoe2': [''],'bpaq_dragon2': [''],'bpaq_kayak2': [''],'bpaq_kite_surf1_2': [''],'bpaq_paddle2': [''],'bpaq_row2': [''],'bpaq_sail2': [''],'bpaq_skull2': [''],'bpaq_surf1_2': [''],'bpaq_surf_comp1_2': [''],'bpaq_wake2': [''],'bpaq_water_ski2': [''],'bpaq_windsurf1_2': [''],'bpaq_body_board_freq_wk2': [''],'bpaq_canoe_freq_wk2': [''],'bpaq_dragon_freq_wk2': [''],'bpaq_kayak_freq_wk2': [''],'bpaq_kite_surf1_freq_wk2': [''],'bpaq_paddle_freq_wk2': [''],'bpaq_row_freq_wk2': [''],'bpaq_sail_freq_wk2': [''],'bpaq_skull_freq_wk2': [''],'bpaq_surf1_freq_wk2': [''],'bpaq_surf_comp1_freq_wk2': [''],'bpaq_wake_freq_wk2': [''],'bpaq_water_ski_freq_wk2': [''],'bpaq_windsurf1_freq_wk2': [''],'bpaq_low_imp2': [''],'bpaq_mod_imp2': [''],'bpaq_high_imp2': [''],'bpaq_low_imp_freq_wk2': [''],'bpaq_mod_imp_freq_wk2': [''],'bpaq_high_imp_freq_wk2': [''],'bpaq_grp_ath3': [''],'bpaq_grp_ball3': [''],'bpaq_grp_bowl3': [''],'bpaq_grp_climb3': [''],'bpaq_grp_cycle3': [''],'bpaq_grp_dance3': [''],'bpaq_grp_football3': [''],'bpaq_grp_gymnastics3': [''],'bpaq_grp_gym3': [''],'bpaq_grp_house3': [''],'bpaq_grp_jump3': [''],'bpaq_grp_lifting3': [''],'bpaq_grp_ma3': [''],'bpaq_grp_occ_act3': [''],'bpaq_grp_rac_sport3': [''],'bpaq_grp_riding3': [''],'bpaq_grp_run3': [''],'bpaq_grp_skate3': [''],'bpaq_grp_snow3': [''],'bpaq_grp_surf3': [''],'bpaq_grp_swim3': [''],'bpaq_grp_throw3': [''],'bpaq_grp_tri3': [''],'bpaq_grp_walk3': [''],'bpaq_grp_water_sport3': [''],'bpaq_grp_other3': [''],'bpaq_ath_jump3': [''],'bpaq_ath_mid3': [''],'bpaq_ath_throw3': [''],'bpaq_ath_hurd3': [''],'bpaq_ath_junior3': [''],'bpaq_jump_freq_wk3': [''],'bpaq_mid_freq_wk3': [''],'bpaq_throw_freq_wk3': [''],'bpaq_hurd_freq_wk3': [''],'bpaq_junior_freq_wk3': [''],'bpaq_ball_baseball3': [''],'bpaq_ball_cric3': [''],'bpaq_ball_f_hoc3': [''],'bpaq_ball_golf_walk3': [''],'bpaq_ball_golf_car3': [''],'bpaq_ball_ice_hoc3': [''],'bpaq_ball_lacr3': [''],'bpaq_ball_soft3': [''],'bpaq_ball_tball3': [''],'bpaq_baseball_freq_wk3': [''],'bpaq_cric_freq_wk3': [''],'bpaq_f_hoc_freq_wk3': [''],'bpaq_golf_walk_freq_wk3': [''],'bpaq_golf_car_freq_wk3': [''],'bpaq_ice_hoc_freq_wk3': [''],'bpaq_lacr_freq_wk3': [''],'bpaq_soft_freq_wk3': [''],'bpaq_tball_freq_wk3': [''],'bpaq_lawn_bowl3': [''],'bpaq_10pin3': [''],'bpaq_lawn_bowl_freq_wk3': [''],'bpaq_10pin_freq_wk3': [''],'bpaq_rock3': [''],'bpaq_gym_climb3': [''],'bpaq_boulder3': [''],'bpaq_rock_freq_wk3': [''],'bpaq_gym_climb_freq_wk3': [''],'bpaq_boulder_freq_wk3': [''],'bpaq_cycle_rec3': [''],'bpaq_cycle_sprint3': [''],'bpaq_cycle_end3': [''],'bpaq_cycle_rec_freq_wk3': [''],'bpaq_cycle_sprint_freq_wk3': [''],'bpaq_cycle_end_freq_wk3': [''],'bpaq_ballet3': [''],'bpaq_ballroom3': [''],'bpaq_cheer3': [''],'bpaq_cont3': [''],'bpaq_high3': [''],'bpaq_hiphop3': [''],'bpaq_jazz3': [''],'bpaq_line3': [''],'bpaq_tap3': [''],'bpaq_ballet_freq_wk3': [''],'bpaq_ballroom_freq_wk3': [''],'bpaq_cheer_freq_wk3': [''],'bpaq_cont_freq_wk3': [''],'bpaq_high_freq_wk3': [''],'bpaq_hiphop_freq_wk3': [''],'bpaq_jazz_freq_wk3': [''],'bpaq_line_freq_wk3': [''],'bpaq_tap_freq_wk3': [''],'bpaq_au_foot3': [''],'bpaq_flag_foot3': [''],'bpaq_oz_tag3': [''],'bpaq_rugby3': [''],'bpaq_rugby_un3': [''],'bpaq_soccer3': [''],'bpaq_foot3': [''],'bpaq_au_foot_freq_wk3': [''],'bpaq_flag_foot_freq_wk3': [''],'bpaq_oz_tag_freq_wk3': [''],'bpaq_rugby_freq_wk3': [''],'bpaq_rugby_un_freq_wk3': [''],'bpaq_soccer_freq_wk3': [''],'bpaq_foot_freq_wk3': [''],'bpaq_acro3': [''],'bpaq_art3': [''],'bpaq_dev3': [''],'bpaq_rhyt3': [''],'bpaq_tramp3': [''],'bpaq_acro_freq_wk3': [''],'bpaq_art_freq_wk3': [''],'bpaq_dev_freq_wk3': [''],'bpaq_rhyt_freq_wk3': [''],'bpaq_tramp_freq_wk3': [''],'bpaq_aero_high3': [''],'bpaq_aero_low3': [''],'bpaq_boot3': [''],'bpaq_cross3': [''],'bpaq_elip3': [''],'bpaq_high_train3': [''],'bpaq_pilates3': [''],'bpaq_res_upp_low3': [''],'bpaq_res_upp3': [''],'bpaq_res_low3': [''],'bpaq_res_light3': [''],'bpaq_res_body3': [''],'bpaq_skip3': [''],'bpaq_spin3': [''],'bpaq_stair3': [''],'bpaq_tread_run3': [''],'bpaq_tread_walk3': [''],'bpaq_yoga3': [''],'bpaq_zumba3': [''],'bpaq_aero_high_freq_wk3': [''],'bpaq_aero_low_freq_wk3': [''],'bpaq_boot_freq_wk3': [''],'bpaq_cross_freq_wk3': [''],'bpaq_elip_freq_wk3': [''],'bpaq_high_train_freq_wk3': [''],'bpaq_pilates_freq_wk3': [''],'bpaq_res_upp_low_freq_wk3': [''],'bpaq_res_upp_freq_wk3': [''],'bpaq_res_low_freq_wk3': [''],'bpaq_res_light_freq_wk3': [''],'bpaq_res_body_freq_wk3': [''],'bpaq_skip_freq_wk3': [''],'bpaq_spin_freq_wk3': [''],'bpaq_stair_freq_wk3': [''],'bpaq_tread_run_freq_wk3': [''],'bpaq_tread_walk_freq_wk3': [''],'bpaq_yoga_freq_wk3': [''],'bpaq_zumba_freq_wk3': [''],'bpaq_house3': [''],'bpaq_gard3': [''],'bpaq_house_freq_wk3': [''],'bpaq_gard_freq_wk3': [''],'bpaq_jumprope3': [''],'bpaq_plyo3': [''],'bpaq_jumprope_freq_wk3': [''],'bpaq_plyo_freq_wk3': [''],'bpaq_power_lift3': [''],'bpaq_res_heavy3': [''],'bpaq_res_light1_3': [''],'bpaq_body_wt3': [''],'bpaq_power_lift_freq_wk3': [''],'bpaq_res_heavy_freq_wk3': [''],'bpaq_res_light1_freq_wk3': [''],'bpaq_body_wt_freq_wk3': [''],'bpaq_aikido3': [''],'bpaq_box3': [''],'bpaq_hapk3': [''],'bpaq_judo3': [''],'bpaq_karate3': [''],'bpaq_kick3': [''],'bpaq_kungfu3': [''],'bpaq_taekwondo3': [''],'bpaq_taichi3': [''],'bpaq_wrest3': [''],'bpaq_aikido_freq_wk3': [''],'bpaq_box_freq_wk3': [''],'bpaq_hapk_freq_wk3': [''],'bpaq_judo_freq_wk3': [''],'bpaq_karate_freq_wk3': [''],'bpaq_kick_freq_wk3': [''],'bpaq_kungfu_freq_wk3': [''],'bpaq_taekwondo_freq_wk3': [''],'bpaq_taichi_freq_wk3': [''],'bpaq_wrest_freq_wk3': [''],'bpaq_occ_light3': [''],'bpaq_occ_heavy3': [''],'bpaq_occ_light_freq_wk3': [''],'bpaq_occ_heavy_freq_wk3': [''],'bpaq_bad3': [''],'bpaq_ping3': [''],'bpaq_rac_ball3': [''],'bpaq_squash3': [''],'bpaq_tennis3': [''],'bpaq_bad_freq_wk3': [''],'bpaq_ping_freq_wk3': [''],'bpaq_rac_ball_freq_wk3': [''],'bpaq_squash_freq_wk3': [''],'bpaq_tennis_freq_wk3': [''],'bpaq_horse3': [''],'bpaq_motor3': [''],'bpaq_horse_freq_wk3': [''],'bpaq_motor_freq_wk3': [''],'bpaq_beach_spr3': [''],'bpaq_cross_count3': [''],'bpaq_marat3': [''],'bpaq_mid_dist3': [''],'bpaq_jog3': [''],'bpaq_sprint3': [''],'bpaq_beach_spr_freq_wk3': [''],'bpaq_cross_count_freq_wk3': [''],'bpaq_marat_freq_wk3': [''],'bpaq_mid_dist_freq_wk3': [''],'bpaq_jog_freq_wk3': [''],'bpaq_sprint_freq_wk3': [''],'bpaq_hock3': [''],'bpaq_ice_skate3': [''],'bpaq_fig_skate3': [''],'bpaq_roll_blade3': [''],'bpaq_roll_derby3': [''],'bpaq_roll_skate3': [''],'bpaq_scoot3': [''],'bpaq_skateboard3': [''],'bpaq_hock_freq_wk3': [''],'bpaq_ice_skate_freq_wk3': [''],'bpaq_fig_skate_freq_wk3': [''],'bpaq_roll_blade_freq_wk3': [''],'bpaq_roll_derby_freq_wk3': [''],'bpaq_roll_skate_freq_wk3': [''],'bpaq_scoot_freq_wk3': [''],'bpaq_skateboard_freq_wk3': [''],'bpaq_cross_ski3': [''],'bpaq_snowshoe3': [''],'bpaq_ski3': [''],'bpaq_sled3': [''],'bpaq_snowboard3': [''],'bpaq_cross_ski_freq_wk3': [''],'bpaq_snowshoe_freq_wk3': [''],'bpaq_ski_freq_wk3': [''],'bpaq_sled_freq_wk3': [''],'bpaq_snowboard_freq_wk3': [''],'bpaq_kite_surf3': [''],'bpaq_surf3': [''],'bpaq_surf_comp3': [''],'bpaq_windsurf3': [''],'bpaq_kite_surf_freq_wk3': [''],'bpaq_surf_freq_wk3': [''],'bpaq_surf_comp_freq_wk3': [''],'bpaq_windsurf_freq_wk3': [''],'bpaq_dive3': [''],'bpaq_swim_rec3': [''],'bpaq_swim_sprint3': [''],'bpaq_swim_lap3': [''],'bpaq_scuba3': [''],'bpaq_snorkel3': [''],'bpaq_syn_swim3': [''],'bpaq_water_aerob3': [''],'bpaq_water_polo3': [''],'bpaq_dive_freq_wk3': [''],'bpaq_swim_rec_freq_wk3': [''],'bpaq_swim_sprint_freq_wk3': [''],'bpaq_swim_lap_freq_wk3': [''],'bpaq_scuba_freq_wk3': [''],'bpaq_snorkel_freq_wk3': [''],'bpaq_syn_swim_freq_wk3': [''],'bpaq_water_aerob_freq_wk3': [''],'bpaq_water_polo_freq_wk3': [''],'bpaq_bball3': [''],'bpaq_beachvol3': [''],'bpaq_handball3': [''],'bpaq_netball3': [''],'bpaq_ult_fris3': [''],'bpaq_volley3': [''],'bpaq_bball_freq_wk3': [''],'bpaq_beachvol_freq_wk3': [''],'bpaq_handball_freq_wk3': [''],'bpaq_netball_freq_wk3': [''],'bpaq_ult_fris_freq_wk3': [''],'bpaq_volley_freq_wk3': [''],'bpaq_tri_rec3': [''],'bpaq_tri_comp3': [''],'bpaq_tri_rec_freq_wk3': [''],'bpaq_tri_comp_freq_wk3': [''],'bpaq_hike3': [''],'bpaq_walk3': [''],'bpaq_mount3': [''],'bpaq_pow_walk3': [''],'bpaq_race_walk3': [''],'bpaq_stair_cl3': [''],'bpaq_hike_freq_wk3': [''],'bpaq_walk_freq_wk3': [''],'bpaq_mount_freq_wk3': [''],'bpaq_race_walk_freq_wk3': [''],'bpaq_pow_walk_freq_wk3': [''],'bpaq_stair_cl_freq_wk3': [''],'bpaq_body_board3': [''],'bpaq_canoe3': [''],'bpaq_dragon3': [''],'bpaq_kayak3': [''],'bpaq_kite_surf1_3': [''],'bpaq_paddle3': [''],'bpaq_row3': [''],'bpaq_sail3': [''],'bpaq_skull3': [''],'bpaq_surf1_3': [''],'bpaq_surf_comp1_3': [''],'bpaq_wake3': [''],'bpaq_water_ski3': [''],'bpaq_windsurf1_3': [''],'bpaq_body_board_freq_wk3': [''],'bpaq_canoe_freq_wk3': [''],'bpaq_dragon_freq_wk3': [''],'bpaq_kayak_freq_wk3': [''],'bpaq_kite_surf1_freq_wk3': [''],'bpaq_paddle_freq_wk3': [''],'bpaq_row_freq_wk3': [''],'bpaq_sail_freq_wk3': [''],'bpaq_skull_freq_wk3': [''],'bpaq_surf1_freq_wk3': [''],'bpaq_surf_comp1_freq_wk3': [''],'bpaq_wake_freq_wk3': [''],'bpaq_water_ski_freq_wk3': [''],'bpaq_windsurf1_freq_wk3': [''],'bpaq_low_imp3': [''],'bpaq_mod_imp3': [''],'bpaq_high_imp3': [''],'bpaq_low_imp_freq_wk3': [''],'bpaq_mod_imp_freq_wk3': [''],'bpaq_high_imp_freq_wk3': [''],'bpaq_miss': [''],'bonespecific_physical_activity_questionnaire_bpaq_complete': ['']
    }
    df = pd.DataFrame(data=d)
    df.set_index('record_id',inplace=True)
    
    redcap_dictionary = setup_redcap_dictionary()
    #print( redcap_dictionary['bpaq_art'][0])
    
    with open(profile) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            key = row[0]
            if (key=='record_id'):
                subject_name = row[2]
            elif (key=='age_enroll'):
                df.at[subject_name, 'age_enroll'] = float(row[2])
            elif ('Parameter' in key or
                  'redcap' in key or
                  'bpaq_grp' in key):
                i=1
                #message('Ignoring ' + key)
            else:
                try:
                    curr = redcap_dictionary[key][0]
                    child = redcap_dictionary[key][1]
                    adult = redcap_dictionary[key][2]
                    #message('Reading  ' + key)
                    df.at[subject_name, curr] =  int(row[2])
                    df.at[subject_name, child] = int(row[3])
                    df.at[subject_name, adult] = int(row[4])
                except KeyError:
                    message('ERROR: ' + key + ' not found and ignored.')
    
    df = df.drop(['tmp'])
    return df

def BPAQ(
    ifile,
    ofile=None,
    show_redcap=False,
    show_table=False,
    print_template=False):

    # Imports
    import argparse
    import os
    import time
    import numpy as np
    import pandas as pd

    set_pandas_display_options()
    individual_report = False
    
    # Get the coefficient table as a DataFrame
    df_table = generate_table()
    
    if (show_table):
        message("Show Table data.")
        print(df_table)
        exit()

    if (print_template):
        message("Printing template for individual profile.")
        print_profile_template(ifile)
        message("Template printed:", ifile)
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
    
    # Read input data
    if ifile.lower().endswith('.txt'):
        message("Reading profile input file:", ifile)
        df = individual_profile_to_dataframe(ifile)
        individual_report = True

    else:
        message("Reading excel input file:", ifile)
        df = pd.read_excel(ifile)
        df.set_index('record_id',inplace=True) # Assign the record ID as the table index
        
    df.fillna(0,inplace=True) # Fill NANs with zeros
    
    # Visual check – this prints the FULL dataframe – caution!
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    #print(df.transpose())
    
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
    if ofile is not None:
        message("Writing output file:", ofile)
        
        df[['redcap_event_name',\
            'bpaq_current_activity',\
            'bpaq_current_num_activity',\
            'bpaq_curr_res',\
            'bpaq_past_child_activity',\
            'bpaq_past_adult_activity',\
            'bpaq_past_res',\
            'bpaq_tot_res']].to_csv(ofile, float_format='%.6g', index=True)  
        #df.to_excel(ofile+'.xlsx', index=True, sheet_name='BPAQ scores')  
        #df.head(15)
    
    if (individual_report):
      subject_name = df.index[0]
      #subject_name = ind.lstrip()
      print(f"----------------------------------------------------------------------------")
      print(f" Name:                    {subject_name.lstrip()}")
      print(f" Age:                     {df.at[subject_name,'age_enroll']:6.2f}")
      print(f" Activity scores")
      print(f"   - current    (12 mo)   {df.at[subject_name,'bpaq_curr_res']:6.2f}")
      print(f"   - childhood (<15yrs)   {df.at[subject_name,'bpaq_past_child_activity']:6.2f}")
      print(f"   - adult     (>15yrs)   {df.at[subject_name,'bpaq_past_adult_activity']:6.2f}")
      print(f" Final score              {df.at[subject_name,'bpaq_tot_res']:6.2f}")
      print(f"----------------------------------------------------------------------------")
    #print(df.transpose())
    

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

Example usage for an input excel sheet:

    blBPAQ bpaq_data_example_input.xlsx -o bpaq_data_example_output.csv

Example usage for an individual profile:

    blBPAQ bpaq_individual_ex01_input.txt -o bpaq_individual_ex01_output.csv
    blBPAQ bpaq_individual_ex01_input.txt
    
A template for an individual profile can be created:

    blBPAQ my_template.txt --print_template

The output for an individual profile is written to the screen, as well as to
a CSV file if an output file is defined. For the results from an excel input
file the output is only created to a CSV file, and the parameters we output
are designed specifically for easy upload to REDCap for our data archive system. 

Hints and tips:

1. You MUST include 'age_enroll' in the input.

2. If you run into problems, try using an Excel sheet with only 30 or
   40 subject data (rows)

3. Sometimes the format of cells can cause a problem (i.e. an integer being
   expressed as a date). Select all the cells and choose a 'number' format.
   
Installation requirements include pandas and xlrd.

Steven Boyd, May 7, 2020.

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blBPAQ",
        description=description
    )
    parser.add_argument('ifile', help='Input Excel file of completed BPAQ instrument')
    parser.add_argument('-o','--ofile',help='Output BPAQ scores')
    parser.add_argument('-t','--show_table',action="store_true",
                        help='Show coefficients (was Table 6) (default: %(default)s)')
    parser.add_argument('-r','--show_redcap',action="store_true",
                        help='Show REDCap variables (default: %(default)s)')
    parser.add_argument('-p','--print_template',action="store_true",
                        help='Print template file for profile (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('BPAQ', vars(args)))

    # Run program
    BPAQ(**vars(args))

if __name__ == '__main__':
    main()

