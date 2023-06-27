{
  inputs = {
    nixpkgs.url = "nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, ... }@inputs:
    inputs.flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = inputs.nixpkgs.legacyPackages."${system}";
      in
      {
        packages.default = pkgs.python3Packages.buildPythonPackage {
          name = "snimpy";
          src = self;
          preConfigure = ''
           # Unfortunately, we cannot build a proper string from what we got in self
           echo "1.0.0-0-000000000000" > version.txt
          '';
          checkPhase = "pytest";
          checkInputs = with pkgs.python3Packages; [ pytest coverage ];
          propagatedBuildInputs = with pkgs.python3Packages; [ cffi pysnmp ipython ];
          buildInputs = with pkgs; [ libsmi pkgs.python3Packages.vcversioner ];
        };
        apps.default = { type = "app"; program = "${self.packages."${system}".default}/bin/snimpy"; };
        devShells.default = pkgs.mkShell {
          name = "snimpy-dev";
          buildInputs = [
            self.packages."${system}".default.inputDerivation
            pkgs.python3Packages.ipython
          ];
        };
      });
}
