import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  cyberZones: [
    { id: 'downtown', name: 'Downtown', security_state: "GREEN", positions: [[19.08, 72.85],[19.085, 72.85],[19.085, 72.865],[19.08, 72.865]] },
    { id: 'midtown', name: 'Midtown', security_state: "RED", positions: [[19.09, 72.86],[19.094, 72.86],[19.094, 72.87],[19.09, 72.87]] },
  ]
};

export const cyberSlice = createSlice({
  name: 'cyber',
  initialState,
  reducers: {
    setCyberZones(state, action) {
      state.cyberZones = action.payload;
    }
  }
});

export const { setCyberZones } = cyberSlice.actions;
export const selectCyberZones = state => state.cyber.cyberZones;
export default cyberSlice.reducer;
