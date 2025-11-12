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

'use client';

import { cn } from '@/libs/utils';

type LozengeAppearance = 'default' | 'success' | 'info' | 'warning' | 'error';

interface LozengeProps {
  appearance?: LozengeAppearance;
  children: React.ReactNode;
  className?: string;
}

/**
 * Lozenge component inspired by Atlassian Design System
 * A subtle status indicator with rounded corners
 */
export function Lozenge({ appearance = 'default', children, className }: LozengeProps) {
  const baseStyles =
    'inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium rounded-md transition-colors';

  const appearanceStyles: Record<LozengeAppearance, string> = {
    default: 'bg-muted text-muted-foreground',
    success: 'bg-success-subtle text-success-subtle-foreground',
    info: 'bg-info-subtle text-info-subtle-foreground',
    warning: 'bg-warning-subtle text-warning-subtle-foreground',
    error: 'bg-error-subtle text-error-subtle-foreground',
  };

  return (
    <span className={cn(baseStyles, appearanceStyles[appearance], className)}>{children}</span>
  );
}
