import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  zones: [
    { id: 'airport', name: 'Airport', color: 'orange', positions: [[19.09, 72.86], [19.10, 72.86], [19.10, 72.88], [19.09, 72.88]] },
  ],
  lightPoles: [
    { id: 1, lat: 19.095, lng: 72.87, status: 'ONLINE', brightness: 80 },
    { id: 2, lat: 19.098, lng: 72.865, status: 'OFFLINE', brightness: 0 },
  ]
};

export const weatherSlice = createSlice({
  name: 'weather',
  initialState,
  reducers: {
    setZones(state, action) {
      state.zones = action.payload;
    },
    setLightPoles(state, action) {
      state.lightPoles = action.payload;
    }
  }
});

export const { setZones, setLightPoles } = weatherSlice.actions;
export const selectZones = state => state.weather.zones;
export const selectLightPoles = state => state.weather.lightPoles;
export default weatherSlice.reducer;
