{
  inputs = {
    nixpkgs.url = "nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, ... }@inputs:
    inputs.flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = inputs.nixpkgs.legacyPackages."${system}";
        checkInputs = with pkgs.python3Packages; [ pytest coverage ];
        buildInputs = with pkgs.python3Packages; [ pkgs.libsmi vcversioner ];
        propagatedBuildInputs = with pkgs.python3Packages; [ cffi pysnmp-lextudio ipython ];
      in
      {
        packages.default = pkgs.python3Packages.buildPythonPackage {
          inherit checkInputs buildInputs propagatedBuildInputs;
          name = "snimpy";
          src = self;
          preConfigure = ''
            # Unfortunately, we cannot build a proper string from what we got in self
            echo "1.0.0-0-000000000000" > version.txt
          '';
          checkPhase = "${pkgs.python3Packages.pytest}/bin/pytest";
        };
        apps.default = { type = "app"; program = "${self.packages."${system}".default}/bin/snimpy"; };
        devShells.default = pkgs.mkShell {
          name = "snimpy-dev";
          buildInputs = checkInputs ++ buildInputs ++ propagatedBuildInputs ++
            [
              pkgs.python3Packages.ipython
            ];
        };
      });
}
