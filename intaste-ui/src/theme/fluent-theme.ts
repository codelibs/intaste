// Copyright (c) 2025 CodeLibs
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//     http://www.apache.org/licenses/LICENSE-2.0
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import {
  createLightTheme,
  createDarkTheme,
  type BrandVariants,
  type Theme,
} from '@fluentui/react-components';

// Brand colors based on the original primary color (HSL: 221.2 83.2% 53.3%)
// Converted to HEX: #2563EB (blue)
const intasteBrand: BrandVariants = {
  10: '#020409',
  20: '#0C1A2E',
  30: '#142B4C',
  40: '#1A3A67',
  50: '#1F4A81',
  60: '#245B9C',
  70: '#2563EB', // Primary brand color
  80: '#4B82F1',
  90: '#6FA0F5',
  100: '#91BDF9',
  110: '#B3D7FC',
  120: '#D4ECFF',
  130: '#E9F5FF',
  140: '#F4FAFF',
  150: '#FAFCFF',
  160: '#FFFFFF',
};

// Create light theme
export const intasteLightTheme: Theme = createLightTheme(intasteBrand);

// Create dark theme
export const intasteDarkTheme: Theme = createDarkTheme(intasteBrand);

// Customize themes with additional tokens
intasteLightTheme.colorBrandBackground = intasteBrand[70];
intasteLightTheme.colorBrandBackgroundHover = intasteBrand[80];
intasteLightTheme.colorBrandBackgroundPressed = intasteBrand[60];

intasteDarkTheme.colorBrandBackground = intasteBrand[80];
intasteDarkTheme.colorBrandBackgroundHover = intasteBrand[90];
intasteDarkTheme.colorBrandBackgroundPressed = intasteBrand[70];

// Export default theme (light)
export const defaultTheme = intasteLightTheme;
