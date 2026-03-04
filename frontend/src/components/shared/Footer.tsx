import React from "react";

const Footer: React.FC = () => (
  <footer className="text-center py-4 text-gray-400 text-sm">
    © {new Date().getFullYear()} Mumbai Smart City. All rights reserved.
  </footer>
);

export default Footer;
