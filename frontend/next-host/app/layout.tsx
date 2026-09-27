import type {ReactNode} from 'react';
import '../../public/styles.css';
export const metadata = {title: 'Open Source Accounting', description: 'Free AI chat and annual accounting Agent workflows.'};
export default function Layout({children}: {children:ReactNode}) {
  return <html lang="en"><body><a className="skip" href="#main">Skip to content</a>{children}</body></html>;
}
