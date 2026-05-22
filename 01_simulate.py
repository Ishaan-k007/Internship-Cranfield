import sys
import csv
import pandas as pd
import os

# === CONFIGURATION — edit these paths to match your OpenVSP installation ===
OPENVSP_PYTHON_PATH = r"C:\OpenVSP\OpenVSP-3.43.0-win64\python\openvsp"
OPENVSP_BIN_PATH    = r"C:\OpenVSP\OpenVSP-3.43.0-win64\python\openvsp\openvsp"
RESULTS_DIR         = r"C:\Results_Internship"
# ===========================================================================

sys.path.append(OPENVSP_PYTHON_PATH)
import vsp

vsp.SetVSPAEROPath(OPENVSP_BIN_PATH)


# Analysis conditions
aoas = [0,4,8,12,16]
mach = 0.17


# Design parameter ranges
camber_list = [0, 0.02, 0.04, 0.06]
cloc_list = [0.3, 0.4, 0.5]
tc_list = [0.09, 0.12, 0.15]
# need to vary the aoa ,span, 
# Wing constants
spans = [2,6,8,12,16]
root_chords = [1,1.5,2,2.5,3]
tip_chords = [0.2,0.6,1,1.4,1.8]
recref = 4.4631e+6
df = pd.DataFrame(columns=["Angle of attack","Span","Root Chord","Tip Chord","Camber", "Camber_Loc", "Thickness", "CL", "CD", "L/D"])
# Loop through param combinations
for aoa in aoas:
    for i in range(len(spans)):
        span = spans[i]
        root_chord = root_chords[i]
        tip_chord = tip_chords[i]
        bref = span  # total span
        sref = 0.5 * (root_chord + tip_chord) * span  # trapezoidal area

        taper_ratio = tip_chord / root_chord
        cref = (2/3) * root_chord * (1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)

        for m in camber_list:
            for p in cloc_list:
                for t in tc_list:
                    print(f"\n Running: camber={m}%, cloc={p}, thickness={t}")

                    try:
                        vsp.ClearVSPModel()
                        wing_id = vsp.AddGeom("WING")
                        vsp.SetGeomName(wing_id, "ParametricWing")

                        # Set wing shape
                        #print("no")
                        vsp.SetParmVal(wing_id, "Sym_Planar_Flag", "Sym", vsp.SYM_XZ)
                        #print("HI1")
                    

                        vsp.SetParmVal(wing_id, "SectTess_U", "XSec_1", 20)
                        vsp.SetParmVal(wing_id, "Span", "XSec_1", span)
                        #print("HI2")
                        vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 0.0)
                        #print("HI3")
                        vsp.SetParmVal(wing_id, "Dihedral", "XSec_1", 1.0)
                        #print("HI4")
                        vsp.SetParmVal(wing_id, "Twist", "XSec_1", -2.0)
                        #print("HI5")
                        vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", root_chord)
                        
                        vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", tip_chord)

                        # Set airfoil type and parameters
                        xsecsurf_id = vsp.GetXSecSurf(wing_id, 0)

                        # Change root and tip shapes
                        vsp.ChangeXSecShape(xsecsurf_id, 0, vsp.XS_FOUR_SERIES)
                        vsp.ChangeXSecShape(xsecsurf_id, 1, vsp.XS_FOUR_SERIES)
                        vsp.Update()

                        # Get section IDs
                        xsec_id_root = vsp.GetXSec(xsecsurf_id, 0)
                        xsec_id_tip = vsp.GetXSec(xsecsurf_id, 1)

                        # Set NACA parameters at root
                        camber = vsp.GetXSecParm(xsec_id_root, "Camber")
                        camber_loc = vsp.GetXSecParm(xsec_id_root, "CamberLoc")
                        thickness = vsp.GetXSecParm(xsec_id_root, "ThickChord")

                        vsp.SetParmVal(camber, m)
                        vsp.SetParmVal(camber_loc, p)
                        vsp.SetParmVal(thickness, t)

                        # Set NACA parameters at tip
                        camber = vsp.GetXSecParm(xsec_id_tip, "Camber")
                        camber_loc = vsp.GetXSecParm(xsec_id_tip, "CamberLoc")
                        thickness = vsp.GetXSecParm(xsec_id_tip, "ThickChord")

                        vsp.SetParmVal(camber, m)
                        vsp.SetParmVal(camber_loc, p)
                        vsp.SetParmVal(thickness, t)
                        vsp.Update()

                     

                        
                        
                        output_dir = RESULTS_DIR
                        os.makedirs(output_dir, exist_ok=True)

                        # Save geometry for checking
                        vsp_filename = os.path.join(output_dir, f"vspaero_geom_c{m}_cloc{p}_t{t}.vsp3")
                        vsp.WriteVSPFile(vsp_filename, vsp.SET_ALL)
                        print(f" Saved geometry to {vsp_filename}")

                        # Save VSPAERO analysis run file
                        output_dir = OPENVSP_BIN_PATH
                        os.makedirs(output_dir, exist_ok=True)
                        
                        
                        vsp_run_filename = os.path.join(output_dir, "vspaero_run.vsp3")
                        vsp.SetVSP3FileName(vsp_run_filename)
                        vsp.WriteVSPFile(vsp_run_filename, vsp.SET_ALL)
                        print(f" Saved VSPAERO run file to {vsp_run_filename}")
                        # === VSPAERO Compute Geometry ===
                        try:
                            compgeom_name = "VSPAEROComputeGeometry"
                            vsp.SetAnalysisInputDefaults(compgeom_name)
                            method = list(vsp.GetIntAnalysisInput(compgeom_name, "AnalysisMethod"))
                            method[0] = vsp.VORTEX_LATTICE
                            vsp.SetIntAnalysisInput(compgeom_name, "AnalysisMethod", method)
                            vsp.ExecAnalysis(compgeom_name)
                        except:
                            print("HI10")
                        

                        # === VSPAERO Sweep ===
                        analysis_name = "VSPAEROSweep"
                        vsp.SetAnalysisInputDefaults(analysis_name)
                        vsp.SetIntAnalysisInput(analysis_name, "GeomSet", [0])
                        

                        # Set RefFlag = 0 (Manual input of ref values)
                        vsp.SetIntAnalysisInput(analysis_name, "RefFlag", [0])

                        # Now set your reference values
                        vsp.SetDoubleAnalysisInput(analysis_name, "Sref", [sref])
                        vsp.SetDoubleAnalysisInput(analysis_name, "Cref", [cref])
                        vsp.SetDoubleAnalysisInput(analysis_name, "Bref", [bref])
                        #set int is for integers set double is for decimal points 
                        vsp.SetDoubleAnalysisInput(analysis_name, "AlphaStart", [aoa])
                        vsp.SetDoubleAnalysisInput(analysis_name, "MachStart", [mach])
                        vsp.SetDoubleAnalysisInput(analysis_name, "AlphaEnd", [aoa])
                        vsp.SetIntAnalysisInput(analysis_name, "AlphaNpts", [1])
                        vsp.SetDoubleAnalysisInput(analysis_name,"ReCref", [4463100])
                        
                        vsp.Update()
                        result_id = vsp.ExecAnalysis(analysis_name)

                        # Get and save results
                        try:
                            print(" Available results:")
                            history_res = vsp.FindLatestResultsID("VSPAERO_History")
                            print(history_res)
                            cl_vals = vsp.GetDoubleResults(history_res, "CL")
                            cd_vals = vsp.GetDoubleResults(history_res, "CDi")
                            
                        
                            cdo_vals = vsp.GetDoubleResults(history_res,"CDo")
                            CDtot = vsp.GetDoubleResults(history_res, "CDtot",0)
                            L2D = vsp.GetDoubleResults(history_res, "L/D",0)
                           
                            
                        

                            if cl_vals and cd_vals:
                                CL = cl_vals[-1]
                                CD = cd_vals[0] + cdo_vals[-1]
                                L_D = CL / CD if CD != 0 else 0

                                

                                print(f" Done: CL={CL:.4f}, CD={CD:.4f}, L/D={L_D:.2f}")
                                new_row = {"Angle of attack":aoa,"Span":span,"Root Chord":root_chord,"Tip Chord":tip_chord,"Camber":m, "Camber_Loc":p, "Thickness":t, "CL":CL, "CD":CD, "L/D":L_D}
                                
                                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)    
                            
                                
                            else:
                                raise ValueError("Missing CL/CD values in VSPAERO results")

                        except Exception as e:
                            print(f" Error for camber={m}, cloc={p}, thickness={t}: {e}")

                    except Exception as e:
                        print(f" Error for camber={m}, cloc={p}, thickness={t}: {e}")
print(df)
output_dir = RESULTS_DIR
os.makedirs(output_dir, exist_ok=True)
csv_path = os.path.join(output_dir, "vspaero_results.csv")
df.to_csv(csv_path, index=False)