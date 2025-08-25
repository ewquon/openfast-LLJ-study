#!/usr/bin/env python
import os
import glob
from shutil import copytree
import numpy as np
import xarray as xr

# https://github.com/nrel/windtools
#from windtools.common import calc_wind
def calc_wind(ds):
    u = ds['u']
    v = ds['v']
    wspd = np.sqrt(u**2 + v**2)
    wdir = 180. + np.degrees(np.arctan2(u, v))
    return wspd, wdir

#========================
# case setup
zhub = 150.
Drotor = 240.
rotorlo = zhub-Drotor/2
rotorhi = zhub+Drotor/2
suffix = '_classC'
#========================

template_dir = f'template{suffix}'
conditions = [f'mon{suffix}',f'mon_veer{suffix}',f'llj{suffix}']

def setup(ncfile,casedir='newcase',prefix=None,monotonic_veer=True):
    inflow = {}
    if prefix is None:
        prefix = os.path.split(casedir)[1]

    copytree(template_dir,f'{casedir}')
    for cond in conditions:
        os.makedirs(f'{casedir}/{cond}/inflow',exist_ok=True)
    
    ds = xr.open_dataset(ncfile)
    ds = ds.rename_vars(t_sec='t').swap_dims(t='t')
    Tmax = ds.t[-1]
    print(Tmax,'(not used)')

    ds_mon = ds.rename({'u_mon':'u', 'v_mon':'v'})[['u','v']]
    inflow[f'mon{suffix}'] = ds_mon

    # check reference wind speed for power-law profile
    Uhub = ds_mon['u'].sel(z=150.0,drop=True)
    Upow = Uhub * (ds.coords['z']/150.0)**0.2
    assert np.allclose(Upow.transpose('t','z'), ds_mon['u'].transpose('t','z'))

    # rotate so that hub-height wind is from 270 deg
    ds_llj = ds.rename({'u_llj':'u', 'v_llj':'v'})[['u','v']]
    wspd,wdir = calc_wind(ds_llj)
    orig_wdir = wdir.sel(z=zhub)
    offset = np.radians(270.0 - orig_wdir)
    rotated_u =  ds_llj['u'] * np.cos(offset) + ds_llj['v'] * np.sin(offset)
    rotated_v = -ds_llj['u'] * np.sin(offset) + ds_llj['v'] * np.cos(offset)
    ds_llj['u'] = rotated_u
    ds_llj['v'] = rotated_v
    inflow[f'llj{suffix}'] = ds_llj

    # add veer to monotonic case
    if monotonic_veer:
        assert np.all(ds_mon['v']==0)
        _,dir_llj = calc_wind(ds_llj)
        offset = np.radians(270.0 - dir_llj)
        rotated_u = ds_mon['u'] * np.cos(offset)
        rotated_v = ds_mon['u'] * np.sin(offset)
        ds_mon_veer = ds_mon.copy()
        ds_mon_veer['u'] = rotated_u
        ds_mon_veer['v'] = rotated_v
        inflow[f'mon_veer{suffix}'] = ds_mon_veer

    # load input file templates
    profilefile = f'{casedir}/UserWind.profiles'
    with open(profilefile,'r') as f:
        usrwind_tmpl = ''.join(f.readlines())
    os.remove(profilefile)

    turbsimfile = f'{casedir}/classC.inp'
    with open(turbsimfile,'r') as f:
        turbsim_tmpl = ''.join(f.readlines())
    os.remove(turbsimfile)

    inflowfile = f'{casedir}/InflowFile.dat'
    with open(inflowfile,'r') as f:
        inflow_tmpl = ''.join(f.readlines())
    os.remove(inflowfile)

    fastfile = f'{casedir}/iea15mw.fst'
    with open(fastfile,'r') as f:
        fst_tmpl = ''.join(f.readlines())
    os.remove(fastfile)

    # write input file templates
    for cond in conditions:

        # downselect to hourly
        times = np.arange(0,inflow[cond].coords['t'][-1],3600)

        for itime,ti in enumerate(times):
            ds = inflow[cond].interp(t=ti)
            wspd,wdir = calc_wind(ds)
            header = usrwind_tmpl.format(Description=cond,
                                         NumUSRz=ds.dims['z'])
            profilefile_relpath = f'UserWind_{itime:02d}.profile'
            profilefile = f'{casedir}/{cond}/inflow/{profilefile_relpath}'
            with open(profilefile,'w') as f:
                f.write(header)
                for ws,wd in zip(wspd,wdir):
                    f.write(f'{ws.z.item():g} {ws.item():g} {270.0-wd.item():g}\n')
            print('Wrote',profilefile)

            for iseed in range(6):
                prefix = f'iea15mw_{itime:02d}_seed{iseed}'
                seed = 42 * 2**iseed # shrug

                inp = turbsim_tmpl.format(
                        RandSeed1=seed, ProfileFile=profilefile_relpath)
                turbsimfile = f'{casedir}/{cond}/inflow/{prefix}.inp'
                with open(turbsimfile,'w') as f:
                    f.write(inp)
                print('Wrote',turbsimfile)

                btsfile_relpath = f'inflow/{prefix}.bts'
                inp = inflow_tmpl.format(btsfile=btsfile_relpath)
                inflowfile = f'{casedir}/{cond}/InflowFile_{prefix}.dat'
                with open(inflowfile,'w') as f:
                    f.write(inp)
                print('Wrote',inflowfile) 

                inflowfile_relpath = os.path.split(inflowfile)[1]
                fst = fst_tmpl.replace('"{InflowFile}"',f'"{inflowfile_relpath}"')
                fstfile = f'{casedir}/{cond}/{prefix}.fst'
                with open(fstfile,'w') as f:
                    f.write(fst)
                print('Wrote',fstfile) 


#==============================================================================
if __name__ == '__main__':

    datadir = 'inflowdata'

    setup(f'{datadir}/April5.nc', casedir='April5_classC', prefix='20200405')
    setup(f'{datadir}/May15.nc',  casedir='May15_classC',  prefix='20200515')
    setup(f'{datadir}/June3.nc',  casedir='June3_classC',  prefix='20200603')

