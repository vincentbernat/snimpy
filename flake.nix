{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, ... }@inputs:
    inputs.flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = inputs.nixpkgs.legacyPackages."${system}";
      in
      rec {
        defaultPackage = pkgs.python3Packages.buildPythonPackage rec {
          name = "snimpy";
          src = self;
          preConfigure = ''
           # Unfortunately, we cannot build a proper string from what we got in self
           echo "1.0.0-0-000000000000" > version.txt
          '';
          checkPhase = "pytest";
          checkInputs = with pkgs.python3Packages; [ pytest mock coverage ];
          propagatedBuildInputs = with pkgs.python3Packages; [ cffi pysnmp ipython ];
          buildInputs = with pkgs; [ libsmi pkgs.python3Packages.vcversioner ];
        };
        defaultApp = { type = "app"; program = "${defaultPackage}/bin/snimpy"; };
      });
}
