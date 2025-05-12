{
  description = "HTTP ForwardAuth middleware for wake-on-LAN";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    treefmt-nix.url = "github:numtide/treefmt-nix";
  };

  outputs =
    { self, ... }@inputs:
    inputs.flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = inputs.nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python311.withPackages (ps: [
          ps.flask
        ]);
      in
      {
        devShell = pkgs.mkShell {
          NIX_CONFIG = "extra-experimental-features = nix-command flakes";

          buildInputs = [ pythonEnv ];

          nativeBuildInputs = builtins.attrValues {
            inherit (pkgs)
              black
              isort
              jsonfmt
              nixfmt
              ;
          };
        };

        formatter = inputs.treefmt-nix.lib.mkWrapper pkgs {
          projectRootFile = "flake.nix";
          programs = {
            black.enable = true;
            isort.enable = true;
            jsonfmt.enable = true;
            nixfmt.enable = true;
          };
        };

        defaultApp = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "run-http-wol" ''
            cd ${self}
            ${pythonEnv}/bin/python http-wol.py "$@"
          ''}/bin/run-http-wol";
        };
      }
    );
}
