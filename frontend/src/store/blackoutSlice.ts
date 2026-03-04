import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  blackoutZones: [
    { id: 'z1', name: 'Zone 1', status: 'ONLINE', positions: [[19.091, 72.881],[19.094, 72.881],[19.094, 72.886],[19.091, 72.886]] },
    { id: 'z2', name: 'Zone 2', status: 'OFFLINE', positions: [[19.089, 72.889],[19.092, 72.889],[19.092, 72.894],[19.089, 72.894]] },
  ]
};

export const blackoutSlice = createSlice({
  name: 'blackout',
  initialState,
  reducers: {
    setBlackoutZones(state, action) {
      state.blackoutZones = action.payload;
    }
  }
});

export const { setBlackoutZones } = blackoutSlice.actions;
export const selectBlackoutZones = state => state.blackout.blackoutZones;
export default blackoutSlice.reducer;
