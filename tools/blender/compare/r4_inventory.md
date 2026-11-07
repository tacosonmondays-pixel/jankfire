# Round 4 props: inventory

Every Blender world prop the maps place (`node tools/blender/props_r4.mjs --md`), most copies first. Copies are
across all maps (Plant & Defuse layouts included); triangles and materials are read from each model's file. One
draw call per prop, material (after merging plain ones) and LOD covers every copy on a map.

| prop | copies | model | lod0 / lod1 tris | materials (near / far) | kB | maps |
|---|---|---|---|---|---|---|
| pine | 2536 | `p_pine` | 248 / 24 | pn_tree / pn_tree | 30 | forest 2536 |
| lollipop | 1641 | `p_lollipop` | 387 / 40 | tint+lp_bark / tint+lp_bark | 37 | warehouse_sd 512, warehouse 491, suburb_sd 213, suburb 206, jankburg 68, skyline 49, skyline_sd 39, rooftop_sd 29, rooftop 25, range 9 |
| streetlight | 1374 | `p_streetlight` | 822 / 86 | sl_steel+glow / sl_steel+glow | 63 | skyline 369, skyline_sd 352, rooftop 231, rooftop_sd 227, jankburg 62, warehouse 49, warehouse_sd 49, suburb 20, suburb_sd 15 |
| conifer | 1131 | `p_conifer` | 276 / 40 | cf_tree / cf_tree | 29 | warehouse_sd 449, warehouse 430, suburb_sd 115, suburb 103, range 21, jankburg 13 |
| car | 690 | `p_car_sedan / p_car_hatch / p_car_taxi (p_car)` | 3398 / 290 | ind+lamp+tint+glass+trim+tail / tint+trim | 317 | skyline_sd 182, skyline 179, rooftop 130, rooftop_sd 129, jankburg 26, suburb 19, suburb_sd 17, warehouse 4, warehouse_sd 4 |
| crate | 435 | `p_crate` | 486 / 12 | cr_wood+cr_steel / cr_wood | 138 | skyline_sd 78, skyline 66, rooftop_sd 58, warehouse 55, rooftop 43, warehouse_sd 27, desert_sd 24, desert 20, bazaar_sd 20, islands 11, deadmall 9, suburb 6, suburb_sd 6, crate 4, bazaar 3, jankburg 3, forest 2 |
| cardboard | 276 | `p_cardboard` | 96 / 12 | cb_card+cb_tape / cb_card | 64 | warehouse 186, warehouse_sd 79, jankburg 10, suburb 1 |
| pallet | 275 | `p_pallet` | 264 / 12 | pl_wood / pl_wood | 46 | warehouse 147, warehouse_sd 117, suburb 11 |
| fern | 183 | `p_fern` | 116 / 12 | fn_fern / fn_fern | 14 | forest 183 |
| bush | 142 | `p_bush` | 120 / 12 | bs_bush / bs_bush | 13 | forest 142 |
| barrel | 104 | `p_barrel` | 592 / 32 | tint+br_label / tint | 38 | jankburg 58, desert_sd 13, warehouse_sd 9, desert 9, warehouse 6, bazaar 4, suburb_sd 3, bazaar_sd 2 |
| acunit | 87 | `p_acunit` | 580 / 36 | ac_metal+ac_paint / ac_paint | 65 | rooftop_sd 29, rooftop 26, skyline_sd 17, skyline 15 |
| barrier | 77 | `p_barrier` | 196 / 28 | jb_concrete / jb_concrete | 34 | jankburg 40, warehouse 14, warehouse_sd 10, suburb_sd 8, skyline 3, skyline_sd 2 |
| palm | 74 | `p_palm` | 378 / 38 | pm_tree / pm_tree | 37 | desert 32, desert_sd 24, bazaar 12, rooftop 4, rooftop_sd 2 |
| birch | 74 | `p_birch` | 324 / 36 | bc_tree / bc_tree | 36 | forest 74 |
| deadtree | 68 | `p_deadtree` | 362 / 36 | dt_tree / dt_tree | 36 | forest 68 |
| billboard_post | 62 | `p_billboard_post` | 184 / 24 | bb_steel / bb_steel | 23 | rooftop_sd 10, platform 8, jankburg 8, warehouse 6, warehouse_sd 6, skyline 6, skyline_sd 6, range 6, rooftop 2, suburb 2, suburb_sd 2 |
| stall | 54 | `p_stall` | 1492 / 94 | st_wood+tint+st_brass / st_wood+tint | 132 | jankburg 32, bazaar 16, bazaar_sd 4, desert 2 |
| hay | 53 | `p_hay` | 540 / 28 | hy_straw / hy_straw | 42 | desert 26, desert_sd 21, bazaar 3, bazaar_sd 3 |
| pot | 41 | `p_pot` | 524 / 60 | pt_clay / pt_clay | 34 | jankburg 25, bazaar 12, desert 2, bazaar_sd 2 |
| container | 38 | `p_container` | 1932 / 12 | ct_steel+tint+ct_decal / tint | 184 | warehouse_sd 17, warehouse 14, platform 3, desert 3, desert_sd 1 |
| billboard | 31 | `p_billboard` | 584 / 68 | bb_steel+glow / bb_steel | 58 | rooftop_sd 5, platform 4, jankburg 4, warehouse 3, warehouse_sd 3, skyline 3, skyline_sd 3, range 3, rooftop 1, suburb 1, suburb_sd 1 |
| pallet_load (round 1) | 31 | `p_pallet_load` | 460 / 24 | pll_wood+pll_film / pll_wood+pll_film | 99 | warehouse 11, warehouse_sd 10, jankburg 5, suburb_sd 3, suburb 2 |
| rack (round 1) | 30 | `p_rack` | 1868 / - | rk_upright+rk_steel+rk_blue+rk_beam+rk_deck+rk_sign / - | 93 | warehouse 22, warehouse_sd 8 |
| vending | 27 | `p_vending` | 360 / 36 | tint+vd_trim+glow / tint+glow | 50 | jankburg 27 |
| cone | 26 | `p_cone` | 364 / 42 | cn_plastic / cn_plastic | 28 | warehouse 10, warehouse_sd 10, suburb 6 |
| camel | 22 | `p_camel` | 1496 / 144 | cm_main+tint / cm_main+tint | 101 | desert_sd 7, desert 5, bazaar 5, bazaar_sd 5 |
| tent | 22 | `p_tent` | 1106 / 136 | tn_main+tn_brass+tint / tn_main+tint | 102 | desert 10, bazaar_sd 6, desert_sd 3, bazaar 3 |
| grave | 22 | `p_grave` | 590 / 40 | gr_main / gr_main | 46 | desert 12, desert_sd 10 |
| saguaro | 19 | `p_saguaro` | 358 / 40 | sg_cactus / sg_cactus | 23 | desert 12, desert_sd 7 |
| forklift (round 1) | 16 | `p_forklift` | 10802 / - | fk_yellow+fk_counter+fk_hazard+fk_sticker+fk_black+fk_seat+fk_steel+fk_knob0+fk_knob1+fk_knob2+fk_lamp+fk_beacon+fk_chrome+fk_tire+fk_rim / - | 411 | warehouse 7, warehouse_sd 6, jankburg 3 |
| watertower | 15 | `p_watertower` | 1126 / 102 | wt_steel+wt_wood / wt_wood+wt_steel | 117 | skyline 6, rooftop_sd 5, rooftop 2, skyline_sd 2 |
| trailer | 14 | `p_trailer` | 2388 / 188 | tr_body+tr_dark+tr_steel / tr_body+tr_dark | 241 | warehouse_sd 10, warehouse 4 |
| grave_cross | 12 | `p_grave_cross` | 580 / 46 | gr_main / gr_main | 45 | desert 6, desert_sd 6 |
| wagon | 11 | `p_wagon` | 2330 / 194 | wg_wood+wg_iron+wg_canvas / wg_wood+wg_canvas | 196 | desert 7, desert_sd 4 |
| dyevat | 10 | `p_dyevat` | 784 / 34 | vt_stone+tint / vt_stone+tint | 61 | bazaar 6, bazaar_sd 4 |
| bus (round 1) | 7 | `p_bus` | 16188 / - | bus_yellow+bus_black+bus_glass+bus_lettering+bus_chrome+bus_sign+bus_tag+bus_red+bus_amber+bus_head+bus_stop+bus_stop_t+bus_tire+bus_rim / - | 612 | jankburg 6, suburb_sd 1 |
| excavator | 6 | `p_excavator` | 2156 / 100 | ex_dark+ex_paint+ex_chrome / ex_dark+ex_paint | 205 | warehouse 2, warehouse_sd 2, suburb 1, suburb_sd 1 |
| numball (round 1) | 6 | `p_numball` | 21960 / - | nb_shell0+nb_face0+nb_white+nb_black+nb_shell1+nb_face1+nb_shell2+nb_face2+nb_shell3+nb_face3+nb_shell4+nb_face4+nb_shell5+nb_face5+nb_shell6+nb_face6+nb_shell7+nb_face7+nb_shell8+nb_face8+nb_shell9+nb_face9 / - | 597 | jankburg 6 |
| handcart | 5 | `p_handcart` | 1228 / 102 | hc_wood+hc_iron+tint / hc_wood+tint | 111 | bazaar 3, desert 1, bazaar_sd 1 |
| wagon_open | 4 | `p_wagon_open` | 2066 / 156 | wo_wood+wo_iron / wo_wood | 174 | desert 2, desert_sd 2 |
| generator | 3 | `p_generator` | 1424 / 144 | gt_steel+gt_paint+glow / gt_paint+glow | 135 | suburb 1, warehouse 1, warehouse_sd 1 |
| pallet (round 1) | 1 | `p_pallet` | 264 / 12 | pl_wood / pl_wood | 46 | jankburg 1 |
